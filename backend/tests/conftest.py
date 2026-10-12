"""Fixtures compartilhadas.

Testes em tests/integration usam SOMENTE o banco de TEST_DATABASE_URL e só rodam se:
- TEST_DATABASE_URL estiver definida;
- o nome do banco terminar em "_test";
- ele for diferente do banco de DATABASE_URL.
O esquema do banco de teste é apagado e recriado pelas migrações a cada execução.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.core.config import ConfiguracaoInvalida, carregar_configuracoes
from app.db.verificacao import ErroDeConexao, verificar_conexao

ARQUIVO_ALEMBIC = Path(__file__).resolve().parents[1] / "alembic.ini"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)


def _mesmo_banco(a: URL, b: URL) -> bool:
    return (a.host or "localhost", a.port or 5432, a.database) == (
        b.host or "localhost",
        b.port or 5432,
        b.database,
    )


@pytest.fixture(scope="session")
def url_teste() -> URL:
    try:
        cfg = carregar_configuracoes()
    except ConfiguracaoInvalida as erro:
        pytest.skip(f"Testes de integração não executados: {erro}")
    url = cfg.url_banco_teste
    if url is None:
        pytest.skip("Testes de integração não executados: TEST_DATABASE_URL não está definida.")
    if not url.database.endswith("_test"):
        pytest.exit(
            f"Recusado: o banco de teste '{url.database}' não termina em '_test'. "
            "Os testes apagam dados e só rodam num banco exclusivo de testes.",
            returncode=2,
        )
    if _mesmo_banco(url, cfg.url_banco):
        pytest.exit(
            "Recusado: TEST_DATABASE_URL aponta para o mesmo banco de DATABASE_URL.",
            returncode=2,
        )
    return url


def config_alembic(url: URL, conexao: Connection | None = None) -> Config:
    cfg = Config(str(ARQUIVO_ALEMBIC))
    cfg.attributes["url"] = url
    cfg.attributes["configurar_logs"] = False
    if conexao is not None:
        cfg.attributes["connection"] = conexao
    return cfg


def recriar_esquema(engine: Engine, url: URL) -> None:
    with engine.begin() as conexao:
        conexao.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    command.upgrade(config_alembic(url), "head")


@pytest.fixture(scope="session")
def engine(url_teste: URL) -> Iterator[Engine]:
    engine = create_engine(url_teste, connect_args={"connect_timeout": 5})
    try:
        verificar_conexao(engine)
    except ErroDeConexao as erro:
        pytest.exit(f"Testes de integração (TEST_DATABASE_URL): {erro}", returncode=3)
    recriar_esquema(engine, url_teste)
    yield engine
    engine.dispose()


@pytest.fixture
def conexao(engine: Engine) -> Iterator[Connection]:
    """Conexão dentro de uma transação que é desfeita ao final do teste."""
    with engine.connect() as conexao:
        transacao = conexao.begin()
        yield conexao
        transacao.rollback()


@pytest.fixture
def sessao(conexao: Connection) -> Iterator[Session]:
    """Sessão ORM; cada commit vira um SAVEPOINT e tudo é desfeito no final."""
    with Session(bind=conexao, join_transaction_mode="create_savepoint") as sessao:
        yield sessao
