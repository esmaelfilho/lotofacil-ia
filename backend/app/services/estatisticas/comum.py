"""Partes compartilhadas pelos serviços de estatística."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Concurso

DEZENAS = range(1, 26)

# Os "últimos N concursos" seguem a ordem do número do concurso. LIMIT NULL = todos.
CTE_JANELA = """
janela AS (
  SELECT numero, dezenas FROM concursos ORDER BY numero DESC LIMIT :ultimos
)"""


def percentual(parte: int, total: int) -> float:
    return round(parte * 100 / total, 2) if total else 0.0


def contar_concursos(sessao: Session, ultimos: int | None = None) -> int:
    total = sessao.scalar(select(func.count()).select_from(Concurso)) or 0
    return total if ultimos is None else min(total, ultimos)
