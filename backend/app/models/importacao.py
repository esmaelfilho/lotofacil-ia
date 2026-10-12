from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Identity, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ORIGENS = ("ARQUIVO", "API")
SITUACOES = ("EM_ANDAMENTO", "CONCLUIDA", "CONCLUIDA_COM_REJEICOES", "FALHOU")


def _lista_sql(valores: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in valores)


class HistoricoImportacao(Base):
    __tablename__ = "historico_importacoes"
    __table_args__ = (
        CheckConstraint(f"origem IN ({_lista_sql(ORIGENS)})", name="origem"),
        CheckConstraint(f"status IN ({_lista_sql(SITUACOES)})", name="status"),
        CheckConstraint(
            "total_lidos >= 0 AND total_inseridos >= 0 AND total_ignorados >= 0 "
            "AND total_rejeitados >= 0",
            name="totais_nao_negativos",
        ),
        CheckConstraint(
            "finalizada_em IS NULL OR finalizada_em >= iniciada_em", name="periodo"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    origem: Mapped[str] = mapped_column(String(20))
    referencia: Mapped[str] = mapped_column(String(255))
    hash_conteudo: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), server_default="EM_ANDAMENTO")
    total_lidos: Mapped[int] = mapped_column(Integer, server_default="0")
    total_inseridos: Mapped[int] = mapped_column(Integer, server_default="0")
    total_ignorados: Mapped[int] = mapped_column(Integer, server_default="0")
    total_rejeitados: Mapped[int] = mapped_column(Integer, server_default="0")
    mensagem_erro: Mapped[str | None] = mapped_column(Text)
    iniciada_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    finalizada_em: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
