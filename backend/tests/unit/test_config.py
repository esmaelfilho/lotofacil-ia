"""T01 (parte sem banco): validação da configuração e proteção de senhas."""

import logging

import pytest

from app.core.config import (
    ConfiguracaoInvalida,
    Settings,
    carregar_configuracoes,
    mascarar_url,
)
from app.core.logging import FiltroDeSenhas, remover_senhas

URL_OK = "postgresql+psycopg://usuario:SenhaSecreta123@localhost:5432/lotofacil"


@pytest.fixture(autouse=True)
def sem_ambiente(monkeypatch):
    """Isola os testes do .env e das variáveis de ambiente reais."""
    for nome in ("DATABASE_URL", "TEST_DATABASE_URL", "APP_ENV", "LOG_LEVEL"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)


def test_configuracao_valida():
    cfg = carregar_configuracoes(database_url=URL_OK)
    assert cfg.url_banco.database == "lotofacil"
    assert cfg.url_banco_teste is None


def test_database_url_ausente_gera_mensagem_util():
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar_configuracoes()
    assert "DATABASE_URL não foi definida" in str(erro.value)
    assert ".env.example" in str(erro.value)


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///lotofacil.db",
        "postgresql://usuario:SenhaSecreta123@localhost/lotofacil",
        "postgresql+psycopg2://usuario:SenhaSecreta123@localhost/lotofacil",
    ],
)
def test_somente_postgresql_com_psycopg_e_aceito(url):
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar_configuracoes(database_url=url)
    assert "postgresql+psycopg" in str(erro.value)
    assert "SenhaSecreta123" not in str(erro.value)


def test_url_malformada():
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar_configuracoes(database_url="isto nao e uma url")
    assert "não é uma URL de conexão válida" in str(erro.value)


def test_url_sem_banco():
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar_configuracoes(database_url="postgresql+psycopg://u:SenhaSecreta123@localhost")
    assert "nome do banco" in str(erro.value)
    assert "SenhaSecreta123" not in str(erro.value)


def test_test_database_url_tambem_e_validada():
    with pytest.raises(ConfiguracaoInvalida) as erro:
        carregar_configuracoes(database_url=URL_OK, test_database_url="sqlite:///t.db")
    assert "TEST_DATABASE_URL" in str(erro.value)


def test_mascarar_url_esconde_senha():
    assert "SenhaSecreta123" not in mascarar_url(URL_OK)
    assert "***" in mascarar_url(URL_OK)


def test_filtro_de_logs_remove_senha(caplog):
    logger = logging.getLogger("teste.senha")
    caplog.handler.addFilter(FiltroDeSenhas())
    with caplog.at_level(logging.INFO, logger="teste.senha"):
        logger.info("conectando em %s", URL_OK)
    assert "SenhaSecreta123" not in caplog.text
    assert "usuario:***@localhost" in caplog.text


def test_remover_senhas_mantem_texto_sem_url():
    assert remover_senhas("nada a esconder") == "nada a esconder"
