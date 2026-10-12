"""Configuração de logs. Um filtro mascara senhas de URLs de conexão por segurança."""

import logging
import re

# postgresql+psycopg://usuario:senha@host -> postgresql+psycopg://usuario:***@host
_URL_COM_SENHA = re.compile(r"(\b[a-z][a-z0-9+.-]*://[^:/@\s]+:)[^@\s]+@", re.IGNORECASE)


def remover_senhas(texto: str) -> str:
    return _URL_COM_SENHA.sub(r"\1***@", texto)


class FiltroDeSenhas(logging.Filter):
    def filter(self, registro: logging.LogRecord) -> bool:
        mensagem = registro.getMessage()
        limpa = remover_senhas(mensagem)
        if limpa != mensagem:
            registro.msg, registro.args = limpa, None
        return True


def configurar_logs(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    for handler in logging.getLogger().handlers:
        if not any(isinstance(f, FiltroDeSenhas) for f in handler.filters):
            handler.addFilter(FiltroDeSenhas())
