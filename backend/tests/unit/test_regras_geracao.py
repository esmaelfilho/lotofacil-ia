"""Regras (faixas) e sorteio dos jogos, sem banco."""

import pytest

from app.services.erros import ErroDeNegocio
from app.services.estatisticas.perfil import calcular_perfil
from app.services.geracao import sortear_jogos
from app.services.regras import Faixa, atende, validar_faixa
from tests.estatisticas_conhecidas import C1, C5

PARES_7_8 = Faixa("pares", 7, 8)
SOMA = Faixa("soma", 180, 220)


def test_validar_faixa():
    assert validar_faixa("soma", 180, 220) == SOMA
    with pytest.raises(ErroDeNegocio, match="desconhecida"):
        validar_faixa("cor", 1, 2)
    with pytest.raises(ErroDeNegocio, match="mínimo .* maior que o máximo"):
        validar_faixa("pares", 9, 7)
    with pytest.raises(ErroDeNegocio, match="entre 0 e 9"):
        validar_faixa("primos", 0, 10)


def test_atende():
    # C5: 11 pares, soma 184; C1: 7 pares, soma 120
    assert atende(C1, [PARES_7_8], base=C5)
    assert not atende(C1, [PARES_7_8, SOMA], base=C5)
    assert not atende(C5, [PARES_7_8], base=C1)
    assert atende(C5, [Faixa("repetidas_do_concurso_base", 9, 9)], base=C1)  # 9 em comum
    assert atende(C5, [], base=C1)


def test_sorteio_respeita_tudo_e_nao_repete():
    jogos, tentativas = sortear_jogos(
        quantidade=50,
        dezenas_por_jogo=15,
        obrigatorias=[1, 25],
        excluidas=[13, 14],
        faixas=[PARES_7_8, SOMA],
        base=C1,
        semente=42,
    )
    assert len(jogos) == 50 and tentativas >= 50
    assert len({tuple(j) for j in jogos}) == 50
    for j in jogos:
        assert len(j) == 15 and j == sorted(j)
        assert {1, 25} <= set(j) and not {13, 14} & set(j)
        p = calcular_perfil(j)
        assert 7 <= p.pares <= 8 and 180 <= p.soma <= 220


def test_mesma_semente_mesmos_jogos():
    args = dict(
        quantidade=10, dezenas_por_jogo=17, obrigatorias=[5], excluidas=[], faixas=[SOMA], base=C1
    )
    a, _ = sortear_jogos(**args, semente=123)
    b, _ = sortear_jogos(**args, semente=123)
    c, _ = sortear_jogos(**args, semente=124)
    assert a == b and a != c
    assert all(len(j) == 17 for j in a)


def test_regras_impossiveis_devolvem_menos_jogos():
    jogos, tentativas = sortear_jogos(
        quantidade=5,
        dezenas_por_jogo=15,
        obrigatorias=[],
        excluidas=[],
        faixas=[Faixa("pares", 13, 13)],  # só existem 12 dezenas pares
        base=C1,
        semente=1,
        maximo_de_tentativas=2000,
    )
    assert jogos == [] and tentativas == 2000


def test_jogo_unico_possivel():
    # 10 excluídas deixam exatamente 15 dezenas: só um jogo existe
    jogos, _ = sortear_jogos(
        quantidade=2,
        dezenas_por_jogo=15,
        obrigatorias=[],
        excluidas=list(range(16, 26)),
        faixas=[],
        base=C1,
        semente=7,
        maximo_de_tentativas=500,
    )
    assert jogos == [list(range(1, 16))]
