"""Tradução dos erros de negócio em respostas HTTP."""

from fastapi import HTTPException

from app.services.erros import Conflito, ErroDeNegocio, NaoEncontrado


def http(erro: ErroDeNegocio) -> HTTPException:
    if isinstance(erro, NaoEncontrado):
        return HTTPException(404, str(erro))
    if isinstance(erro, Conflito):
        return HTTPException(409, str(erro))
    return HTTPException(422, str(erro))
