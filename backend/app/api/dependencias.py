"""Dependências compartilhadas pelos endpoints."""

from fastapi import Request

from app.core.config import Settings
from app.integracoes.caixa import ClienteCaixa


def obter_cliente_caixa(request: Request) -> ClienteCaixa:
    cfg: Settings = request.app.state.configuracoes
    return ClienteCaixa(
        url_base=cfg.caixa_api_url,
        pausa_segundos=cfg.caixa_pausa_segundos,
        timeout_segundos=cfg.caixa_timeout_segundos,
    )
