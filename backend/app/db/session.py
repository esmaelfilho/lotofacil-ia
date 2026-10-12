"""Criação do engine e das sessões do SQLAlchemy."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker


def criar_engine(url: str | URL, pool_size: int = 5, connect_timeout: int = 5) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=pool_size,
        connect_args={"connect_timeout": connect_timeout},
    )


def criar_fabrica_de_sessoes(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def obter_sessao(request: Request) -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição, sempre fechada no final."""
    fabrica: sessionmaker[Session] = request.app.state.fabrica_de_sessoes
    with fabrica() as sessao:
        yield sessao
