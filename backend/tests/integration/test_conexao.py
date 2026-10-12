"""T01: conexão e mensagens de erro úteis, sem expor a senha."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import carregar_configuracoes
from app.db.session import criar_engine
from app.db.verificacao import ErroDeConexao, verificar_conexao
from app.main import criar_app


def test_conecta_no_banco_de_teste(engine):
    verificar_conexao(engine)


def test_senha_errada_gera_erro_util_sem_mostrar_a_senha(url_teste):
    url = url_teste.set(password="SenhaErradaXYZ")
    engine = criar_engine(url, connect_timeout=3)
    with pytest.raises(ErroDeConexao) as erro:
        verificar_conexao(engine)
    mensagem = str(erro.value)
    assert "usuário ou senha recusados" in mensagem
    assert f"Banco: {url.database}" in mensagem
    assert "SenhaErradaXYZ" not in mensagem


def test_banco_inexistente(url_teste):
    engine = criar_engine(url_teste.set(database="nao_existe_test"), connect_timeout=3)
    with pytest.raises(ErroDeConexao) as erro:
        verificar_conexao(engine)
    assert "não existe" in str(erro.value)


def test_servidor_indisponivel(url_teste):
    engine = criar_engine(url_teste.set(host="127.0.0.1", port=1), connect_timeout=3)
    with pytest.raises(ErroDeConexao) as erro:
        verificar_conexao(engine)
    mensagem = str(erro.value)
    # No Linux a porta fechada é recusada na hora; no Windows o sistema insiste por alguns
    # segundos e a tentativa pode terminar por tempo esgotado. As duas causas são corretas.
    assert "não há servidor PostgreSQL" in mensagem or "não respondeu a tempo" in mensagem, mensagem
    assert url_teste.password not in mensagem


def test_api_saude_responde_conectado(engine, url_teste):
    cfg = carregar_configuracoes(database_url=url_teste.render_as_string(hide_password=False))
    with TestClient(criar_app(cfg)) as cliente:
        resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    assert resposta.json()["banco"] == "conectado"


def test_api_nao_inicia_sem_banco_e_nao_loga_senha(url_teste, caplog):
    url = url_teste.set(password="SenhaErradaXYZ")
    cfg = carregar_configuracoes(database_url=url.render_as_string(hide_password=False))
    with pytest.raises(ErroDeConexao):
        with TestClient(criar_app(cfg)):
            pass
    assert "Não foi possível conectar ao PostgreSQL" in caplog.text
    assert "SenhaErradaXYZ" not in caplog.text
