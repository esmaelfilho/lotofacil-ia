"""Endpoints de regras, estratégias, gerações e conferência."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import carregar_configuracoes
from app.main import criar_app
from app.models import Concurso
from tests.estatisticas_conhecidas import C1, CONCURSOS


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
        # não toca em regras_estatisticas (catálogo da migração 0003)
        conexao.execute(text("TRUNCATE concursos, estrategias RESTART IDENTITY CASCADE"))


def test_fluxo_completo(cliente):
    regras = cliente.get("/regras").json()
    assert len(regras) == 9

    criada = cliente.post(
        "/estrategias",
        json={"nome": "Equilibrada", "regras": [{"codigo": "pares", "minimo": 7, "maximo": 8}]},
    )
    assert criada.status_code == 201
    estrategia = criada.json()
    assert estrategia["regras"] == [{"codigo": "pares", "minimo": 7, "maximo": 8, "nome": "Pares"}]

    resposta = cliente.post(
        "/geracoes",
        json={
            "estrategia_id": estrategia["id"],
            "quantidade": 4,
            "obrigatorias": [3],
            "semente": 10,
        },
    )
    assert resposta.status_code == 201
    gerada = resposta.json()
    assert len(gerada["jogos"]) == 4 and gerada["semente"] == 10
    assert all(3 in j["dezenas"] and 7 <= j["perfil"]["pares"] <= 8 for j in gerada["jogos"])

    lista = cliente.get("/geracoes").json()
    assert lista["total"] >= 1 and lista["itens"][0]["id"] == gerada["id"]
    assert "jogos" not in lista["itens"][0]
    assert cliente.get(f"/geracoes/{gerada['id']}").json()["jogos"] == gerada["jogos"]

    conferencia = cliente.post(f"/geracoes/{gerada['id']}/conferir", params={"concurso": 1}).json()
    assert conferencia["dezenas_sorteadas"] == C1
    assert len(conferencia["jogos"]) == 4

    historico = cliente.post("/jogos/conferir-historico", json={"dezenas": C1}).json()
    assert historico["por_acertos"]["15"] == 2

    assert cliente.delete(f"/estrategias/{estrategia['id']}").status_code == 409
    desativada = cliente.post(f"/estrategias/{estrategia['id']}/desativar").json()
    assert desativada["ativa"] is False and desativada["usada"] is True
    assert cliente.post(f"/estrategias/{estrategia['id']}/ativar").json()["ativa"] is True


def test_erros(cliente):
    assert cliente.get("/estrategias/999").status_code == 404
    assert cliente.get("/geracoes/999").status_code == 404
    assert cliente.post("/geracoes/999/conferir", params={"concurso": 1}).status_code == 404

    invalida = cliente.post(
        "/estrategias",
        json={"nome": "X", "regras": [{"codigo": "pares", "minimo": 9, "maximo": 1}]},
    )
    assert invalida.status_code == 422 and "maior que o máximo" in invalida.json()["detail"]

    assert cliente.post("/geracoes", json={"quantidade": 101}).status_code == 422
    assert cliente.post("/geracoes", json={"obrigatorias": [26]}).status_code == 422
    conflito = cliente.post("/geracoes", json={"obrigatorias": [5], "excluidas": [5]})
    assert conflito.status_code == 422 and "ao mesmo tempo" in conflito.json()["detail"]

    curto = cliente.post("/jogos/conferir-historico", json={"dezenas": [1, 2, 3]})
    assert curto.status_code == 422

    nova = cliente.post("/estrategias", json={"nome": "Temporária"}).json()
    assert cliente.delete(f"/estrategias/{nova['id']}").status_code == 204
    assert cliente.post("/estrategias", json={"nome": "temporária"}).status_code == 201
    assert cliente.post("/estrategias", json={"nome": "TEMPORÁRIA"}).status_code == 409
