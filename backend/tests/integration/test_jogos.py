"""Fase 4: catálogo de regras, estratégias, geração e conferência (PostgreSQL de teste)."""

import pytest
from sqlalchemy import func, select

from app.models import Avaliacao, Concurso, GeracaoJogos, JogoGerado
from app.schemas.jogos import EstrategiaEntrada, FaixaEntrada, GeracaoEntrada
from app.services import avaliacao, estrategias, geracao
from app.services.erros import Conflito, ErroDeNegocio, NaoEncontrado
from app.services.estatisticas.perfil import calcular_perfil
from tests.estatisticas_conhecidas import C1, C5, CONCURSOS


@pytest.fixture
def com_concursos(sessao):
    sessao.add_all(Concurso(numero=n, data_sorteio=d, dezenas=z) for n, d, z in CONCURSOS)
    sessao.commit()
    return sessao


def _estrategia(sessao, nome="Equilibrada", **faixas):
    faixas = faixas or {"pares": (7, 8), "soma": (180, 220)}
    entrada = EstrategiaEntrada(
        nome=nome,
        regras=[FaixaEntrada(codigo=c, minimo=a, maximo=b) for c, (a, b) in faixas.items()],
    )
    return estrategias.criar(sessao, entrada)


def test_catalogo_carregado_pela_migracao(sessao):
    regras = {r.codigo: r for r in estrategias.listar_regras(sessao)}
    assert len(regras) == 9
    assert regras["pares"].parametros_padrao == {"minimo": 7, "maximo": 8}
    assert regras["repetidas_do_concurso_base"].nome == "Repetidas do concurso base"


def test_criar_editar_e_listar_estrategia(sessao):
    criada = _estrategia(sessao)
    assert [(r.codigo, r.minimo, r.maximo) for r in criada.regras] == [
        ("pares", 7, 8),
        ("soma", 180, 220),
    ]
    assert criada.ativa and not criada.usada

    editada = estrategias.atualizar(
        sessao,
        criada.id,
        EstrategiaEntrada(
            nome="Só primos", regras=[FaixaEntrada(codigo="primos", minimo=5, maximo=6)]
        ),
    )
    assert editada.nome == "Só primos"
    assert [r.codigo for r in editada.regras] == ["primos"]
    assert [e.nome for e in estrategias.listar(sessao)] == ["Só primos"]


@pytest.mark.parametrize(
    ("regras", "mensagem"),
    [
        ([("cor", 1, 2)], "desconhecida"),
        ([("pares", 9, 7)], "maior que o máximo"),
        ([("pares", 7, 8), ("pares", 6, 9)], "repetida"),
    ],
)
def test_estrategia_invalida(sessao, regras, mensagem):
    entrada = EstrategiaEntrada(
        nome="X", regras=[FaixaEntrada(codigo=c, minimo=a, maximo=b) for c, a, b in regras]
    )
    with pytest.raises(ErroDeNegocio, match=mensagem):
        estrategias.criar(sessao, entrada)


def test_nome_repetido_e_conflito(sessao):
    _estrategia(sessao, "Minha")
    with pytest.raises(Conflito, match="Já existe"):
        _estrategia(sessao, "minha")


def test_geracao_respeita_regras_e_guarda_copia(com_concursos):
    sessao = com_concursos
    estrategia = _estrategia(sessao)
    gerada = geracao.gerar(
        sessao,
        GeracaoEntrada(
            estrategia_id=estrategia.id,
            quantidade=20,
            obrigatorias=[10],
            excluidas=[25],
            semente=99,
        ),
    )
    assert gerada.concurso_base == 5  # padrão: o último concurso
    assert gerada.semente == 99 and gerada.estrategia_nome == "Equilibrada"
    assert len(gerada.jogos) == 20
    assert [j.sequencia for j in gerada.jogos] == list(range(1, 21))
    assert len({tuple(j.dezenas) for j in gerada.jogos}) == 20
    for j in gerada.jogos:
        assert 10 in j.dezenas and 25 not in j.dezenas
        assert 7 <= j.perfil.pares <= 8 and 180 <= j.perfil.soma <= 220
        assert j.repetidas_do_concurso_base == len(set(j.dezenas) & set(C5))

    # mudar a estratégia depois não muda a geração (cópia dos parâmetros)
    estrategias.atualizar(sessao, estrategia.id, EstrategiaEntrada(nome="Outra", regras=[]))
    relida = geracao.obter(sessao, gerada.id)
    assert relida.estrategia_nome == "Equilibrada"
    assert [r.codigo for r in relida.regras] == ["pares", "soma"]
    assert [j.dezenas for j in relida.jogos] == [j.dezenas for j in gerada.jogos]
    assert estrategias.obter(sessao, estrategia.id).usada


def test_mesma_semente_reproduz_a_geracao(com_concursos):
    entrada = GeracaoEntrada(quantidade=5, dezenas_por_jogo=18, semente=2026)
    a = geracao.gerar(com_concursos, entrada)
    b = geracao.gerar(com_concursos, entrada)
    assert a.id != b.id
    assert [j.dezenas for j in a.jogos] == [j.dezenas for j in b.jogos]
    assert all(len(j.dezenas) == 18 for j in a.jogos)


def test_semente_sorteada_quando_nao_informada(com_concursos):
    gerada = geracao.gerar(com_concursos, GeracaoEntrada(quantidade=1))
    assert gerada.semente is not None and gerada.semente >= 0


def test_regra_repetidas_do_concurso_base(com_concursos):
    estrategia = _estrategia(com_concursos, "Repete 9", repetidas_do_concurso_base=(9, 9))
    gerada = geracao.gerar(
        com_concursos,
        GeracaoEntrada(estrategia_id=estrategia.id, quantidade=10, concurso_base=1, semente=5),
    )
    assert gerada.concurso_base == 1
    assert all(len(set(j.dezenas) & set(C1)) == 9 for j in gerada.jogos)


def test_erros_da_geracao(sessao):
    with pytest.raises(Conflito, match="Atualize os concursos"):
        geracao.gerar(sessao, GeracaoEntrada(quantidade=1))

    sessao.add_all(Concurso(numero=n, data_sorteio=d, dezenas=z) for n, d, z in CONCURSOS)
    sessao.commit()
    with pytest.raises(NaoEncontrado, match="Concurso 4"):
        geracao.gerar(sessao, GeracaoEntrada(concurso_base=4))
    with pytest.raises(NaoEncontrado, match="Estratégia 999"):
        geracao.gerar(sessao, GeracaoEntrada(estrategia_id=999))
    with pytest.raises(ErroDeNegocio, match="ao mesmo tempo: 05"):
        geracao.gerar(sessao, GeracaoEntrada(obrigatorias=[5], excluidas=[5]))
    with pytest.raises(ErroDeNegocio, match="16 obrigatórias para jogos de 15"):
        geracao.gerar(sessao, GeracaoEntrada(obrigatorias=list(range(1, 17))))
    with pytest.raises(ErroDeNegocio, match="sobram menos de 16"):
        geracao.gerar(sessao, GeracaoEntrada(dezenas_por_jogo=16, excluidas=list(range(1, 11))))

    impossivel = _estrategia(sessao, "Impossível", pares=(13, 13))
    with pytest.raises(ErroDeNegocio, match="Só foram encontrados 0 de 3"):
        geracao.gerar(sessao, GeracaoEntrada(estrategia_id=impossivel.id, quantidade=3, semente=1))
    assert sessao.scalar(select(func.count()).select_from(GeracaoJogos)) == 0  # nada gravado

    desativada = estrategias.alterar_ativa(sessao, _estrategia(sessao, "Velha").id, False)
    with pytest.raises(ErroDeNegocio, match="desativada"):
        geracao.gerar(sessao, GeracaoEntrada(estrategia_id=desativada.id))


def test_estrategia_usada_so_pode_ser_desativada(com_concursos):
    sessao = com_concursos
    usada = _estrategia(sessao, "Usada")
    geracao.gerar(sessao, GeracaoEntrada(estrategia_id=usada.id, quantidade=1, semente=3))
    with pytest.raises(Conflito, match="Desative"):
        estrategias.excluir(sessao, usada.id)
    assert not estrategias.alterar_ativa(sessao, usada.id, False).ativa

    nunca_usada = _estrategia(sessao, "Nova")
    estrategias.excluir(sessao, nunca_usada.id)
    with pytest.raises(NaoEncontrado):
        estrategias.obter(sessao, nunca_usada.id)


def test_conferir_geracao_contra_concurso(com_concursos):
    sessao = com_concursos
    gerada = geracao.gerar(sessao, GeracaoEntrada(quantidade=8, semente=11))
    conferencia = avaliacao.conferir_geracao(sessao, gerada.id, 1)  # concurso 1 = 01 a 15
    assert conferencia.dezenas_sorteadas == C1
    for jogo in conferencia.jogos:
        esperado = sorted(set(jogo.dezenas) & set(C1))
        assert jogo.dezenas_acertadas == esperado and jogo.acertos == len(esperado)
    assert sum(conferencia.por_acertos.values()) == 8

    avaliacao.conferir_geracao(sessao, gerada.id, 1)  # conferir de novo não duplica
    assert sessao.scalar(select(func.count()).select_from(Avaliacao)) == 8
    gravadas = sessao.execute(
        select(JogoGerado.dezenas, Avaliacao.acertos).join(
            Avaliacao, Avaliacao.jogo_id == JogoGerado.id
        )
    ).all()
    assert all(a == len(set(d) & set(C1)) for d, a in gravadas)

    with pytest.raises(NaoEncontrado, match="Concurso 4"):
        avaliacao.conferir_geracao(sessao, gerada.id, 4)
    with pytest.raises(NaoEncontrado, match="Geração 999"):
        avaliacao.conferir_geracao(sessao, 999, 1)


def test_conferir_jogo_contra_historico(com_concursos):
    # concursos: 1 = 01-15, 2 = 10-24, 3 = 01-15, 5 = C5
    r = avaliacao.conferir_historico(com_concursos, C1)
    assert r.concursos == 4
    assert r.por_acertos == {11: 0, 12: 0, 13: 0, 14: 0, 15: 2}
    assert (r.maior_acerto, r.ultimo_concurso_com_11_ou_mais) == (15, 3)

    r = avaliacao.conferir_historico(com_concursos, sorted(C5))
    assert r.por_acertos[15] == 1 and r.ultimo_concurso_com_11_ou_mais == 5

    dezesseis = list(range(1, 17))  # 1 e 3: 15; 2: 7 (10-16); 5: 10
    r = avaliacao.conferir_historico(com_concursos, dezesseis)
    assert r.por_acertos == {11: 0, 12: 0, 13: 0, 14: 0, 15: 2}


def test_perfil_do_jogo_usa_mesma_definicao(com_concursos):
    gerada = geracao.gerar(com_concursos, GeracaoEntrada(quantidade=3, semente=8))
    for j in gerada.jogos:
        assert j.perfil.soma == calcular_perfil(j.dezenas).soma


def test_gerar_sem_gravar_e_gravar_depois_repete_os_jogos(com_concursos):
    sessao = com_concursos
    estrategia = _estrategia(sessao)
    antes = sessao.scalar(select(func.count()).select_from(GeracaoJogos))

    previa = geracao.gerar(
        sessao, GeracaoEntrada(estrategia_id=estrategia.id, quantidade=6, gravar=False)
    )
    assert previa.gravada is False and previa.id is None and previa.criada_em is None
    assert all(j.id is None for j in previa.jogos) and len(previa.jogos) == 6
    assert sessao.scalar(select(func.count()).select_from(GeracaoJogos)) == antes
    assert sessao.scalar(select(func.count()).select_from(JogoGerado)) == 0
    assert not estrategias.obter(sessao, estrategia.id).usada

    gravada = geracao.gerar(
        sessao,
        GeracaoEntrada(
            estrategia_id=estrategia.id,
            quantidade=6,
            concurso_base=previa.concurso_base,
            semente=previa.semente,
        ),
    )
    assert gravada.gravada is True and gravada.id is not None
    assert [j.dezenas for j in gravada.jogos] == [j.dezenas for j in previa.jogos]
    assert [j.dezenas for j in geracao.obter(sessao, gravada.id).jogos] == [
        j.dezenas for j in previa.jogos
    ]
