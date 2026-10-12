from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Identity, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegraEstatistica(Base):
    __tablename__ = "regras_estatisticas"
    __table_args__ = (
        CheckConstraint("jsonb_typeof(parametros_padrao) = 'object'", name="parametros_objeto"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(Text)
    parametros_padrao: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    ativa: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class Estrategia(Base):
    __tablename__ = "estrategias"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    ativa: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    criada_em: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    atualizada_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EstrategiaRegra(Base):
    __tablename__ = "estrategia_regras"
    __table_args__ = (
        CheckConstraint("jsonb_typeof(parametros) = 'object'", name="parametros_objeto"),
    )

    estrategia_id: Mapped[int] = mapped_column(
        ForeignKey("estrategias.id", ondelete="CASCADE"), primary_key=True
    )
    regra_id: Mapped[int] = mapped_column(
        ForeignKey("regras_estatisticas.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    parametros: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
