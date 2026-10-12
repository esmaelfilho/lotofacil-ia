"""T02: migrações sobem do zero, descem e sobem de novo, e batem com os modelos."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.db.base import Base
from tests.conftest import config_alembic

TABELAS = {
    "concursos",
    "historico_importacoes",
    "regras_estatisticas",
    "estrategias",
    "estrategia_regras",
    "geracoes_jogos",
    "jogos_gerados",
    "avaliacoes",
}


def test_banco_esta_na_ultima_revisao(engine, url_teste):
    head = ScriptDirectory.from_config(config_alembic(url_teste)).get_current_head()
    with engine.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == head


def test_todas_as_tabelas_existem(engine):
    assert TABELAS <= set(inspect(engine).get_table_names())


def test_modelos_e_banco_nao_tem_diferencas(engine):
    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), Base.metadata)
    assert diferencas == []


def test_downgrade_e_upgrade(engine, url_teste):
    cfg = config_alembic(url_teste)
    command.downgrade(cfg, "base")
    try:
        assert not TABELAS & set(inspect(engine).get_table_names())
        with engine.connect() as conexao:
            existe = conexao.scalar(
                text("SELECT count(*) FROM pg_proc WHERE proname = 'lotofacil_dezenas_validas'")
            )
        assert existe == 0
    finally:
        command.upgrade(cfg, "head")
    assert TABELAS <= set(inspect(engine).get_table_names())
