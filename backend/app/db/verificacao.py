"""Verificações feitas na inicialização: conexão com o banco e migrações pendentes."""

import re
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError

from app.core.logging import remover_senhas

ARQUIVO_ALEMBIC = Path(__file__).resolve().parents[2] / "alembic.ini"


class ErroDeConexao(Exception):
    """Falha ao conectar no banco. A mensagem nunca contém a senha."""


# Mensagens do servidor podem vir em inglês ou traduzidas (ex.: PostgreSQL em português no
# Windows). Na falha de login, o servidor responde antes de combinar a codificação, então os
# acentos podem chegar corrompidos ("autentica\ufffd\ufffdo"). Por isso os padrões evitam
# depender de letras acentuadas.
_PADROES_DE_CAUSA = [
    (
        re.compile(r"password authentication failed|senha falhou|autentica\S*o do tipo senha"),
        "usuário ou senha recusados. Confira o usuário e a senha da URL de conexão no "
        "arquivo .env.",
    ),
    (
        re.compile(r"does not exist|n\S{1,3}o existe"),
        "o banco ou o usuário não existe. Crie-os conforme o README (Preparar o PostgreSQL).",
    ),
    (
        re.compile(r"timeout|timed out|tempo esgotado"),
        "o servidor não respondeu a tempo. Confira host e porta e se há firewall.",
    ),
    (
        re.compile(r"connection refused|could not connect|connection failed|recus"),
        "não há servidor PostgreSQL aceitando conexões nesse host e porta. Confira se "
        "o serviço do PostgreSQL está em execução e se a porta está correta.",
    ),
]


def _causa_provavel(detalhe: str) -> str:
    texto = detalhe.lower()
    for padrao, causa in _PADROES_DE_CAUSA:
        if padrao.search(texto):
            return causa
    return "erro inesperado ao conectar. Veja o detalhe abaixo."


def verificar_conexao(engine: Engine) -> None:
    """Executa SELECT 1. Em caso de falha, levanta ErroDeConexao com mensagem útil."""
    url = engine.url
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except OperationalError as erro:
        detalhe = remover_senhas(str(erro.orig).strip())
        raise ErroDeConexao(
            "Não foi possível conectar ao PostgreSQL.\n"
            f"  Host: {url.host or 'localhost'}  Porta: {url.port or 5432}  "
            f"Banco: {url.database}  Usuário: {url.username}\n"
            f"  Causa provável: {_causa_provavel(detalhe)}\n"
            f"  Detalhe: {detalhe}"
        ) from None


def revisoes_do_banco(engine: Engine) -> tuple[str | None, str | None]:
    """Devolve (revisão atual do banco, revisão mais recente disponível)."""
    roteiro = ScriptDirectory.from_config(Config(str(ARQUIVO_ALEMBIC)))
    with engine.connect() as conexao:
        atual = MigrationContext.configure(conexao).get_current_revision()
    return atual, roteiro.get_current_head()
