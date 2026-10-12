"""Erros de regra de negócio, traduzidos em respostas HTTP pelos routers."""


class ErroDeNegocio(Exception):
    """Pedido inválido (422)."""


class NaoEncontrado(ErroDeNegocio):
    """O registro pedido não existe (404)."""


class Conflito(ErroDeNegocio):
    """O pedido conflita com o estado atual dos dados (409)."""
