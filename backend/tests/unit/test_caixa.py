"""Leitura e validação das respostas da API da Caixa (sem internet)."""

from datetime import date

import pytest

from app.integracoes.caixa import (
    ClienteCaixa,
    DadosInvalidosCaixa,
    ErroFonteExterna,
    converter_resultado,
)
from tests.fakes import EXEMPLO_REAL, URL


def test_converte_resposta_real_da_caixa():
    resultado = converter_resultado(EXEMPLO_REAL)
    assert resultado.numero == 3802
    assert resultado.data_sorteio == date(2026, 10, 11)
    assert resultado.dezenas == [2, 3, 5, 6, 9, 10, 11, 12, 14, 15, 19, 20, 21, 23, 24]


def test_usa_lista_ordenada_e_nao_a_ordem_do_sorteio():
    dados = dict(EXEMPLO_REAL, listaDezenas=list(reversed(EXEMPLO_REAL["listaDezenas"])))
    assert converter_resultado(dados).dezenas == sorted(converter_resultado(dados).dezenas)


@pytest.mark.parametrize(
    "alteracao",
    [
        {"listaDezenas": ["01", "02"]},
        {"listaDezenas": ["01"] * 15},
        {"listaDezenas": [f"{d:02d}" for d in range(12, 27)]},
        {"dataApuracao": "2026-10-11"},
        {"numero": "abc"},
    ],
)
def test_dados_invalidos_sao_rejeitados(alteracao):
    with pytest.raises(DadosInvalidosCaixa):
        converter_resultado(dict(EXEMPLO_REAL, **alteracao))


def test_formato_diferente_e_erro_da_fonte():
    dados = dict(EXEMPLO_REAL)
    del dados["listaDezenas"]
    with pytest.raises(ErroFonteExterna, match="formato pode ter mudado"):
        converter_resultado(dados)


def test_resposta_que_nao_e_objeto():
    with pytest.raises(ErroFonteExterna):
        converter_resultado(["não", "é", "objeto"])


def test_cliente_tenta_de_novo_em_falha_temporaria():
    chamadas = []

    def buscar(url):
        chamadas.append(url)
        if len(chamadas) == 1:
            raise ErroFonteExterna("instável")
        return EXEMPLO_REAL

    cliente = ClienteCaixa(url_base=URL, buscar=buscar, pausa_segundos=0, tentativas=3)
    assert cliente.ultimo_concurso().numero == 3802
    assert len(chamadas) == 2


def test_cliente_desiste_depois_das_tentativas():
    def buscar(url):
        raise ErroFonteExterna("fora do ar")

    cliente = ClienteCaixa(url_base=URL, buscar=buscar, pausa_segundos=0, tentativas=2)
    with pytest.raises(ErroFonteExterna, match="fora do ar"):
        cliente.ultimo_concurso()


def test_concurso_diferente_do_pedido_e_rejeitado():
    cliente = ClienteCaixa(url_base=URL, buscar=lambda url: EXEMPLO_REAL, pausa_segundos=0)
    with pytest.raises(DadosInvalidosCaixa, match="pedimos o concurso 10"):
        cliente.concurso(10)
