"""T09: integridade dos relacionamentos (RESTRICT, CASCADE e regras de geração)."""

from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    Avaliacao,
    Concurso,
    Estrategia,
    EstrategiaRegra,
    GeracaoJogos,
    JogoGerado,
    RegraEstatistica,
)

DEZENAS = list(range(1, 16))


@pytest.fixture
def cenario(sessao):
    concurso = Concurso(numero=1, data_sorteio=date(2003, 9, 29), dezenas=DEZENAS)
    regra = RegraEstatistica(codigo="PARES_IMPARES", nome="Pares e ímpares")
    estrategia = Estrategia(nome="Equilíbrio")
    sessao.add_all([concurso, regra, estrategia])
    sessao.flush()
    sessao.add(EstrategiaRegra(estrategia_id=estrategia.id, regra_id=regra.id, parametros={"pares": [7, 8]}))
    geracao = GeracaoJogos(
        estrategia_id=estrategia.id,
        concurso_base_numero=1,
        quantidade_jogos=1,
        parametros={"regras": ["PARES_IMPARES"]},
    )
    sessao.add(geracao)
    sessao.flush()
    jogo = JogoGerado(geracao_id=geracao.id, sequencia=1, dezenas=list(range(11, 26)))
    sessao.add(jogo)
    sessao.flush()
    sessao.add(Avaliacao(jogo_id=jogo.id, concurso_id=concurso.id, acertos=5))
    sessao.commit()
    return {"concurso": concurso, "regra": regra, "estrategia": estrategia, "geracao": geracao}


def _contar(sessao, modelo):
    return sessao.scalar(select(func.count()).select_from(modelo))


def test_concurso_usado_nao_pode_ser_excluido(sessao, cenario):
    sessao.delete(cenario["concurso"])
    with pytest.raises(IntegrityError, match="fk_"):
        sessao.commit()


def test_regra_em_uso_nao_pode_ser_excluida(sessao, cenario):
    sessao.delete(cenario["regra"])
    with pytest.raises(IntegrityError, match="fk_estrategia_regras_regra_id"):
        sessao.commit()


def test_estrategia_usada_em_geracao_nao_pode_ser_excluida(sessao, cenario):
    sessao.delete(cenario["estrategia"])
    with pytest.raises(IntegrityError, match="fk_geracoes_jogos_estrategia_id"):
        sessao.commit()


def test_excluir_geracao_remove_jogos_e_avaliacoes(sessao, cenario):
    sessao.delete(cenario["geracao"])
    sessao.commit()
    sessao.expire_all()
    assert _contar(sessao, JogoGerado) == 0
    assert _contar(sessao, Avaliacao) == 0
    assert _contar(sessao, Concurso) == 1


def test_geracao_exige_concurso_base_existente(sessao):
    sessao.add(GeracaoJogos(concurso_base_numero=999, quantidade_jogos=1, parametros={}))
    with pytest.raises(IntegrityError, match="fk_geracoes_jogos_concurso_base_numero"):
        sessao.commit()


@pytest.mark.parametrize(
    ("campos", "restricao"),
    [
        ({"dezenas_obrigatorias": [1, 2], "dezenas_excluidas": [2, 3]}, "obrigatorias_excluidas_disjuntas"),
        ({"dezenas_excluidas": list(range(1, 12))}, "ck_geracoes_jogos_excluidas"),
        ({"dezenas_por_jogo": 21}, "ck_geracoes_jogos_dezenas_por_jogo"),
        ({"quantidade_jogos": 0}, "ck_geracoes_jogos_quantidade_positiva"),
        ({"parametros": []}, "ck_geracoes_jogos_parametros_objeto"),
    ],
)
def test_regras_da_geracao(sessao, cenario, campos, restricao):
    dados = {"concurso_base_numero": 1, "quantidade_jogos": 1, "parametros": {}} | campos
    sessao.add(GeracaoJogos(**dados))
    with pytest.raises(IntegrityError, match=restricao):
        sessao.commit()


def test_jogo_repetido_na_mesma_geracao(sessao, cenario):
    sessao.add(JogoGerado(geracao_id=cenario["geracao"].id, sequencia=2, dezenas=list(range(11, 26))))
    with pytest.raises(IntegrityError, match="uq_jogos_gerados_geracao_id_dezenas"):
        sessao.commit()


def test_jogo_aceita_ate_20_dezenas(sessao, cenario):
    sessao.add(JogoGerado(geracao_id=cenario["geracao"].id, sequencia=2, dezenas=list(range(1, 21))))
    sessao.commit()
    sessao.add(JogoGerado(geracao_id=cenario["geracao"].id, sequencia=3, dezenas=list(range(1, 22))))
    with pytest.raises(IntegrityError, match="ck_jogos_gerados_dezenas"):
        sessao.commit()
