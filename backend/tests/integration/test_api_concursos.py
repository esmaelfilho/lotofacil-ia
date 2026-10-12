"""Endpoints de concursos e importações, com a API da Caixa simulada."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.dependencias import obter_cliente_caixa
from app.core.config import carregar_configuracoes
from app.integracoes.caixa import ErroFonteExterna
from app.main import criar_app
from tests.fakes import CaixaFalsa


@pytest.fixture
def api(engine, url_teste):
    """API real ligada ao banco de teste; as tabelas são limpas ao final."""
    cfg = carregar_configuracoes(database_url=url_teste.render_as_string(hide_password=False))
    app = criar_app(cfg)
    caixa = CaixaFalsa(ultimo=12)
    app.dependency_overrides[obter_cliente_caixa] = caixa.cliente
    with TestClient(app) as cliente:
        yield cliente, app, caixa
    with engine.begin() as conexao:
        conexao.execute(
            text("TRUNCATE concursos, historico_importacoes RESTART IDENTITY CASCADE")
        )


def test_atualizar_listar_e_consultar(api):
    cliente, _, _ = api
    resposta = cliente.post("/concursos/atualizar")
    assert resposta.status_code == 200
    assert resposta.json()["inseridos"] == 12

    pagina = cliente.get("/concursos", params={"limite": 5}).json()
    assert pagina["total"] == 12
    assert [c["numero"] for c in pagina["itens"]] == [12, 11, 10, 9, 8]

    concurso = cliente.get("/concursos/3").json()
    assert concurso["numero"] == 3 and len(concurso["dezenas"]) == 15

    assert cliente.get("/concursos/999").status_code == 404

    historico = cliente.get("/importacoes").json()
    assert historico[0]["status"] == "CONCLUIDA"
    assert historico[0]["total_inseridos"] == 12


def test_clicar_de_novo_nao_duplica(api):
    cliente, _, _ = api
    cliente.post("/concursos/atualizar")
    segunda = cliente.post("/concursos/atualizar").json()
    assert segunda["inseridos"] == 0
    assert cliente.get("/concursos").json()["total"] == 12


def test_caixa_fora_do_ar_responde_502(api):
    cliente, app, _ = api

    def fora_do_ar(url):
        raise ErroFonteExterna("tempo esgotado")

    app.dependency_overrides[obter_cliente_caixa] = lambda: CaixaFalsa(0).cliente().__class__(
        url_base="x", buscar=fora_do_ar, pausa_segundos=0, tentativas=1
    )
    resposta = cliente.post("/concursos/atualizar")
    assert resposta.status_code == 502
    assert "Não foi possível consultar a Caixa" in resposta.json()["detail"]
