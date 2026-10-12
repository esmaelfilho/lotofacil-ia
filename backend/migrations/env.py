"""Ambiente do Alembic.

A URL vem de `config.attributes["url"]` (usado pelos testes) ou, por padrão, de
DATABASE_URL lida pelas configurações da aplicação. Ela nunca é escrita em arquivo.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  (registra as tabelas em Base.metadata)
from app.core.config import carregar_configuracoes
from app.db.base import Base

config = context.config

if config.config_file_name is not None and config.attributes.get("configurar_logs", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url():
    return config.attributes.get("url") or carregar_configuracoes().url_banco


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conexao = config.attributes.get("connection")
    if conexao is not None:
        _executar(conexao)
        return
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as conexao:
        _executar(conexao)
    engine.dispose()


def _executar(conexao) -> None:
    context.configure(connection=conexao, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
