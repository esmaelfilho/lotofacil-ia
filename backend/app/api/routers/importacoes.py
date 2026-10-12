"""Histórico das importações e atualizações de concursos."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import obter_sessao
from app.models import HistoricoImportacao
from app.schemas.importacao import ImportacaoSaida

router = APIRouter(prefix="/importacoes", tags=["importações"])


@router.get("", response_model=list[ImportacaoSaida])
def listar_importacoes(
    limite: int = Query(20, ge=1, le=200), sessao: Session = Depends(obter_sessao)
) -> list[ImportacaoSaida]:
    """As execuções mais recentes primeiro."""
    registros = sessao.scalars(
        select(HistoricoImportacao).order_by(HistoricoImportacao.id.desc()).limit(limite)
    ).all()
    return [ImportacaoSaida.model_validate(r) for r in registros]
