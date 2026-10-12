from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Identity, Integer, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.tipos import Dezenas, regra_dezenas


class Concurso(Base):
    __tablename__ = "concursos"
    __table_args__ = (
        CheckConstraint("numero > 0", name="numero_positivo"),
        CheckConstraint(regra_dezenas("dezenas", 15, 15), name="dezenas"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True)
    data_sorteio: Mapped[date] = mapped_column(Date, index=True)
    dezenas: Mapped[list[int]] = mapped_column(Dezenas)
    importacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("historico_importacoes.id", ondelete="SET NULL"), index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
