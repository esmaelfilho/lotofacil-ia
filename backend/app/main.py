"""Ponto de entrada da API.

Na inicialização: carrega e valida a configuração, testa a conexão com o PostgreSQL e
avisa se há migrações pendentes. As migrações nunca são aplicadas automaticamente.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import (
    concursos,
    estatisticas,
    estrategias,
    geracoes,
    importacoes,
    saude,
)
from app.core.config import ConfiguracaoInvalida, Settings, mascarar_url, obter_configuracoes
from app.core.logging import configurar_logs
from app.db.session import criar_engine, criar_fabrica_de_sessoes
from app.db.verificacao import ErroDeConexao, revisoes_do_banco, verificar_conexao

log = logging.getLogger("lotofacil")


def criar_app(configuracoes: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
        configurar_logs()
        try:
            cfg = configuracoes or obter_configuracoes()
        except ConfiguracaoInvalida as erro:
            log.error("%s", erro)
            raise
        logging.getLogger().setLevel(cfg.log_level)
        engine = criar_engine(
            cfg.url_banco, cfg.database_pool_size, cfg.database_connect_timeout
        )
        log.info("Conectando ao banco %s", mascarar_url(cfg.url_banco))
        try:
            verificar_conexao(engine)
        except ErroDeConexao as erro:
            log.error("%s", erro)
            engine.dispose()
            raise
        atual, mais_recente = revisoes_do_banco(engine)
        if atual != mais_recente:
            log.warning(
                "O banco está na revisão %s, mas a mais recente é %s. "
                "Rode 'alembic upgrade head' dentro da pasta backend.",
                atual or "(vazio)",
                mais_recente,
            )
        app.state.configuracoes = cfg
        app.state.engine = engine
        app.state.fabrica_de_sessoes = criar_fabrica_de_sessoes(engine)
        log.info("API pronta.")
        yield
        engine.dispose()

    app = FastAPI(
        title="Lotofácil IA",
        description=(
            "Estatísticas e geração de jogos da Lotofácil. Cada sorteio é independente: "
            "as estatísticas descrevem o passado e não aumentam a chance de acerto."
        ),
        version="0.1.0",
        lifespan=ciclo_de_vida,
    )
    app.include_router(saude.router)
    app.include_router(concursos.router)
    app.include_router(importacoes.router)
    app.include_router(estatisticas.router)
    app.include_router(estrategias.router)
    app.include_router(geracoes.router)
    return app


app = criar_app()
