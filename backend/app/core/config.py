"""Configuração centralizada, lida de variáveis de ambiente e do arquivo .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

# O .env fica na raiz do repositório: backend/app/core/config.py -> raiz
RAIZ_DO_PROJETO = Path(__file__).resolve().parents[3]
ARQUIVO_ENV = RAIZ_DO_PROJETO / ".env"

DRIVER_ESPERADO = "postgresql+psycopg"
EXEMPLO_URL = "postgresql+psycopg://usuario:senha@localhost:5432/lotofacil"


class ConfiguracaoInvalida(Exception):
    """Configuração ausente ou inválida. A mensagem nunca contém senhas."""


def converter_url(valor: str, variavel: str) -> URL:
    """Valida uma URL de conexão e devolve o objeto URL do SQLAlchemy."""
    try:
        url = make_url(valor)
    except ArgumentError:
        raise ValueError(
            f"{variavel} não é uma URL de conexão válida. Formato esperado: {EXEMPLO_URL}"
        ) from None
    if url.drivername != DRIVER_ESPERADO:
        raise ValueError(
            f"{variavel} usa '{url.drivername}', mas o projeto aceita somente PostgreSQL "
            f"com o driver Psycopg 3 ('{DRIVER_ESPERADO}://'). Formato esperado: {EXEMPLO_URL}"
        )
    if not url.database:
        raise ValueError(f"{variavel} não informa o nome do banco. Formato esperado: {EXEMPLO_URL}")
    return url


def mascarar_url(url: str | URL) -> str:
    """Representação segura da URL, com a senha trocada por ***."""
    if isinstance(url, str):
        try:
            url = make_url(url)
        except ArgumentError:
            return "<URL inválida>"
    return url.render_as_string(hide_password=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ARQUIVO_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: str
    test_database_url: str | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_connect_timeout: int = Field(default=5, ge=1, le=60)
    app_env: Literal["desenvolvimento", "teste", "producao"] = "desenvolvimento"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def _validar_database_url(cls, valor: str) -> str:
        converter_url(valor, "DATABASE_URL")
        return valor

    @field_validator("test_database_url")
    @classmethod
    def _validar_test_database_url(cls, valor: str | None) -> str | None:
        if valor:
            converter_url(valor, "TEST_DATABASE_URL")
        return valor or None

    @property
    def url_banco(self) -> URL:
        return make_url(self.database_url)

    @property
    def url_banco_teste(self) -> URL | None:
        return make_url(self.test_database_url) if self.test_database_url else None


def carregar_configuracoes(**valores) -> Settings:
    """Carrega as configurações e transforma erros de validação em mensagens úteis."""
    try:
        return Settings(**valores)
    except ValidationError as erro:
        linhas = []
        for item in erro.errors(include_input=False, include_url=False):
            campo = str(item["loc"][0]).upper() if item["loc"] else "configuração"
            if item["type"] == "missing":
                linhas.append(
                    f"- {campo} não foi definida. Crie o arquivo .env a partir do "
                    f".env.example (em {RAIZ_DO_PROJETO}) ou defina a variável de ambiente."
                )
            else:
                mensagem = item["msg"].removeprefix("Value error, ")
                linhas.append(f"- {campo}: {mensagem}")
        raise ConfiguracaoInvalida(
            "Configuração inválida:\n" + "\n".join(linhas)
        ) from None


@lru_cache
def obter_configuracoes() -> Settings:
    return carregar_configuracoes()
