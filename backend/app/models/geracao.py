from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.tipos import Dezenas, regra_dezenas


class GeracaoJogos(Base):
    __tablename__ = "geracoes_jogos"
    __table_args__ = (
        CheckConstraint("quantidade_jogos > 0", name="quantidade_positiva"),
        CheckConstraint("dezenas_por_jogo BETWEEN 15 AND 20", name="dezenas_por_jogo"),
        CheckConstraint(regra_dezenas("dezenas_obrigatorias", 0, 20), name="obrigatorias"),
        CheckConstraint(regra_dezenas("dezenas_excluidas", 0, 10), name="excluidas"),
        CheckConstraint(
            "NOT (dezenas_obrigatorias && dezenas_excluidas)",
            name="obrigatorias_excluidas_disjuntas",
        ),
        CheckConstraint(
            "cardinality(dezenas_obrigatorias) <= dezenas_por_jogo", name="obrigatorias_cabem"
        ),
        CheckConstraint(
            "25 - cardinality(dezenas_excluidas) >= dezenas_por_jogo",
            name="excluidas_permitem_jogo",
        ),
        CheckConstraint("jsonb_typeof(parametros) = 'object'", name="parametros_objeto"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    estrategia_id: Mapped[int | None] = mapped_column(
        ForeignKey("estrategias.id", ondelete="RESTRICT"), index=True
    )
    concurso_base_numero: Mapped[int] = mapped_column(
        ForeignKey("concursos.numero", ondelete="RESTRICT"), index=True
    )
    quantidade_jogos: Mapped[int] = mapped_column(Integer)
    dezenas_por_jogo: Mapped[int] = mapped_column(SmallInteger, server_default="15")
    dezenas_obrigatorias: Mapped[list[int]] = mapped_column(
        Dezenas, server_default=text("'{}'::smallint[]")
    )
    dezenas_excluidas: Mapped[list[int]] = mapped_column(
        Dezenas, server_default=text("'{}'::smallint[]")
    )
    parametros: Mapped[dict[str, Any]] = mapped_column(JSONB)
    semente: Mapped[int | None] = mapped_column(BigInteger)
    criada_em: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class JogoGerado(Base):
    __tablename__ = "jogos_gerados"
    __table_args__ = (
        CheckConstraint("sequencia > 0", name="sequencia_positiva"),
        CheckConstraint(regra_dezenas("dezenas", 15, 20), name="dezenas"),
        UniqueConstraint("geracao_id", "sequencia"),
        UniqueConstraint("geracao_id", "dezenas"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    geracao_id: Mapped[int] = mapped_column(ForeignKey("geracoes_jogos.id", ondelete="CASCADE"))
    sequencia: Mapped[int] = mapped_column(Integer)
    dezenas: Mapped[list[int]] = mapped_column(Dezenas)


class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    __table_args__ = (
        CheckConstraint("acertos BETWEEN 0 AND 15", name="acertos"),
        UniqueConstraint("jogo_id", "concurso_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    jogo_id: Mapped[int] = mapped_column(ForeignKey("jogos_gerados.id", ondelete="CASCADE"))
    concurso_id: Mapped[int] = mapped_column(
        ForeignKey("concursos.id", ondelete="RESTRICT"), index=True
    )
    acertos: Mapped[int] = mapped_column(SmallInteger)
    avaliada_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
