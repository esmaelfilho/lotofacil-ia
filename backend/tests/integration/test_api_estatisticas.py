"""Endpoints de estatística, com o conjunto conferido à mão."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import carregar_configuracoes
from app.main import criar_app
from app.models import Concurso
from tests.estatisticas_conhecidas import CONCURSOS


@pytest.fixture(scope="module")
def cliente(engine, url_teste):
    with engine.begin() as conexao:
        conexao.execute(
            Concurso.__table__.insert(),
            [{"numero": n, "data_sorteio": d, "dezenas": z} for n, d, z in CONCURSOS],
        )
    cfg = carregar_configuracoes(database_url=url_teste.render_as_string(hide_password=False))
    with TestClient(criar_app(cfg)) as cliente:
        yield cliente
    with engine.begin() as conexao:
        conexao.execute(text("TRUNCATE concursos RESTART IDENTITY CASCADE"))


def test_frequencia(cliente):
    r = cliente.get("/estatisticas/frequencia")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["concursos"] == 4 and corpo["janelas"] == [10, 50, 100]
    assert corpo["dezenas"][9] == {
        "dezena": 10,
        "total": 4,
        "percentual": 100.0,
        "janelas": {"10": 4, "50": 4, "100": 4},
    }
    r = cliente.get("/estatisticas/frequencia", params={"janelas": [2]})
    assert r.json()["dezenas"][3]["janelas"] == {"2": 1}
    assert cliente.get("/estatisticas/frequencia", params={"janelas": [0]}).status_code == 422


def test_quentes_frias_e_atrasos(cliente):
    r = cliente.get("/estatisticas/quentes-frias", params={"janela": 4, "quantidade": 3}).json()
    assert [q["dezena"] for q in r["quentes"]] == [10, 12, 14]
    assert [f["dezena"] for f in r["frias"]] == [25, 17, 19]

    atrasos = cliente.get("/estatisticas/atrasos").json()["dezenas"]
    assert atrasos[24] == {
        "dezena": 25,
        "atraso_atual": 4,
        "maior_atraso": 4,
        "ultimo_concurso": None,
    }


def test_perfil_e_distribuicao(cliente):
    pagina = cliente.get("/estatisticas/perfil", params={"limite": 1}).json()
    assert pagina["total"] == 4
    assert pagina["itens"][0]["numero"] == 5
    assert pagina["itens"][0]["perfil"]["soma"] == 184
    assert pagina["itens"][0]["repetidas_do_anterior"] == 9

    r = cliente.get("/estatisticas/distribuicao", params={"caracteristica": "pares"}).json()
    assert [(v["valor"], v["concursos"]) for v in r["valores"]] == [(7, 2), (8, 1), (11, 1)]
    errado = cliente.get("/estatisticas/distribuicao", params={"caracteristica": "cor"})
    assert errado.status_code == 422


def test_obrigatorias_excluidas(cliente):
    r = cliente.get(
        "/estatisticas/obrigatorias-excluidas", params={"obrigatorias": [1], "excluidas": [16]}
    )
    assert r.status_code == 200
    assert r.json()["concursos_atendidos"] == 2

    errado = cliente.get(
        "/estatisticas/obrigatorias-excluidas", params={"obrigatorias": [5], "excluidas": [5]}
    )
    assert errado.status_code == 422
    assert "ao mesmo tempo" in errado.json()["detail"]


def test_combinacoes(cliente):
    r = cliente.get("/estatisticas/combinacoes", params={"tamanho": 3, "quantidade": 1}).json()
    assert r["combinacoes"] == [{"dezenas": [10, 12, 14], "vezes": 4, "percentual": 100.0}]
    assert cliente.get("/estatisticas/combinacoes", params={"tamanho": 4}).status_code == 422
