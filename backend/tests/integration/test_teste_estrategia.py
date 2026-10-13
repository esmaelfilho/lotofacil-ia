"""Testar estratégias em um concurso que já saiu (RF-07), no PostgreSQL de teste."""

import pytest
from sqlalchemy import func, select

from app.models import Avaliacao, Concurso, GeracaoJogos
from app.schemas.jogos import (
    EntradaTesteEstrategia,
    EstrategiaEntrada,
    FaixaEntrada,
    GeracaoEntrada,
)
from app.services import estrategias, geracao, teste_estrategia
from app.services.erros import ErroDeNegocio, NaoEncontrado
from tests.estatisticas_conhecidas import C1, C3, C5, CONCURSOS


@pytest.fixture
def com_concursos(sessao):
    sessao.add_all(Concurso(numero=n, data_sorteio=d, dezenas=z) for n, d, z in CONCURSOS)
    sessao.commit()
    return sessao


def _estrategia(sessao, nome, **faixas):
    return estrategias.criar(
        sessao,
        EstrategiaEntrada(
            nome=nome,
            regras=[FaixaEntrada(codigo=c, minimo=a, maximo=b) for c, (a, b) in faixas.items()],
        ),
    )


def test_base_e_o_concurso_anterior_e_acertos_conferem(com_concursos):
    sessao = com_concursos
    repete = _estrategia(sessao, "Repete 10", repetidas_do_concurso_base=(10, 10))
    pares = _estrategia(sessao, "Pares", pares=(7, 8))

    # não existe o concurso 4: a base do 5 é o 3
    teste = teste_estrategia.testar(
        sessao,
        EntradaTesteEstrategia(
            concurso=5, estrategia_ids=[repete.id, pares.id], quantidade=8, semente=7
        ),
    )
    assert teste.concurso == 5 and teste.concurso_base == 3 and teste.semente == 7
    assert teste.dezenas_sorteadas == C5
    assert [r.estrategia_nome for r in teste.resultados] == ["Repete 10", "Pares", None]

    for resultado in teste.resultados:
        assert len(resultado.jogos) == 8 and resultado.aviso is None
        for jogo in resultado.jogos:
            # acertos conferidos direto em Python
            assert jogo.dezenas_acertadas == sorted(set(jogo.dezenas) & set(C5))
            assert jogo.acertos == len(jogo.dezenas_acertadas)
        acertos = [j.acertos for j in resultado.jogos]
        assert resultado.maior_acerto == max(acertos)
        assert resultado.media_acertos == round(sum(acertos) / len(acertos), 2)
        assert resultado.por_acertos == {p: acertos.count(p) for p in (11, 12, 13, 14, 15)}

    # a regra "repetidas" usou o concurso anterior (3), não o testado (5)
    assert all(len(set(j.dezenas) & set(C3)) == 10 for j in teste.resultados[0].jogos)


def test_nada_e_gravado(com_concursos):
    teste_estrategia.testar(com_concursos, EntradaTesteEstrategia(concurso=2, quantidade=3))
    assert com_concursos.scalar(select(func.count()).select_from(GeracaoJogos)) == 0
    assert com_concursos.scalar(select(func.count()).select_from(Avaliacao)) == 0


def test_mesma_semente_repete_o_teste(com_concursos):
    entrada = EntradaTesteEstrategia(concurso=3, quantidade=4, dezenas_por_jogo=17, semente=11)
    a = teste_estrategia.testar(com_concursos, entrada)
    b = teste_estrategia.testar(com_concursos, entrada)
    assert [j.dezenas for j in a.resultados[0].jogos] == [j.dezenas for j in b.resultados[0].jogos]
    assert all(len(j.dezenas) == 17 for j in a.resultados[0].jogos)


def test_gravar_depois_repete_os_jogos_do_teste(com_concursos):
    sessao = com_concursos
    pares = _estrategia(sessao, "Pares", pares=(7, 8))
    teste = teste_estrategia.testar(
        sessao,
        EntradaTesteEstrategia(
            concurso=5, estrategia_ids=[pares.id], quantidade=5, obrigatorias=[10], semente=3
        ),
    )
    gravada = geracao.gerar(
        sessao,
        GeracaoEntrada(
            estrategia_id=pares.id,
            quantidade=teste.quantidade,
            dezenas_por_jogo=teste.dezenas_por_jogo,
            obrigatorias=teste.obrigatorias,
            excluidas=teste.excluidas,
            concurso_base=teste.concurso_base,
            semente=teste.semente,
        ),
    )
    assert [j.dezenas for j in gravada.jogos] == [j.dezenas for j in teste.resultados[0].jogos]


def test_faixa_impossivel_vira_aviso_sem_erro(com_concursos):
    impossivel = _estrategia(com_concursos, "Impossível", pares=(13, 13))
    teste = teste_estrategia.testar(
        com_concursos,
        EntradaTesteEstrategia(concurso=2, estrategia_ids=[impossivel.id], quantidade=2, semente=1),
    )
    impossivel_r, aleatorio = teste.resultados
    assert impossivel_r.jogos == [] and impossivel_r.maior_acerto is None
    assert "Só foram encontrados 0 de 2" in impossivel_r.aviso
    assert len(aleatorio.jogos) == 2 and aleatorio.aviso is None


def test_erros_do_teste(com_concursos):
    sessao = com_concursos
    with pytest.raises(NaoEncontrado, match="Concurso 4"):
        teste_estrategia.testar(sessao, EntradaTesteEstrategia(concurso=4))
    with pytest.raises(ErroDeNegocio, match="anterior ao 1"):
        teste_estrategia.testar(sessao, EntradaTesteEstrategia(concurso=1))
    with pytest.raises(ErroDeNegocio, match="pelo menos uma"):
        teste_estrategia.testar(sessao, EntradaTesteEstrategia(concurso=2, incluir_aleatorio=False))
    with pytest.raises(NaoEncontrado, match="Estratégia 999"):
        teste_estrategia.testar(sessao, EntradaTesteEstrategia(concurso=2, estrategia_ids=[999]))
    with pytest.raises(ErroDeNegocio, match="obrigatória e excluída"):
        teste_estrategia.testar(
            sessao, EntradaTesteEstrategia(concurso=2, obrigatorias=[5], excluidas=[5])
        )
    desativada = _estrategia(sessao, "Velha", pares=(7, 8))
    estrategias.alterar_ativa(sessao, desativada.id, False)
    with pytest.raises(ErroDeNegocio, match="desativada"):
        teste_estrategia.testar(
            sessao, EntradaTesteEstrategia(concurso=2, estrategia_ids=[desativada.id])
        )


def test_c1_e_c3_iguais_fazem_15_pontos(com_concursos):
    # o concurso 3 repete o 1: um jogo com as dezenas do 1 faria 15 pontos no 3
    teste = teste_estrategia.testar(
        com_concursos, EntradaTesteEstrategia(concurso=3, obrigatorias=C1, quantidade=1)
    )
    assert teste.resultados[0].jogos[0].acertos == 15
    assert teste.resultados[0].por_acertos[15] == 1
