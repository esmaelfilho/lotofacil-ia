"""Endpoints de concursos: listar, consultar e atualizar pela API da Caixa."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencias import obter_cliente_caixa
from app.db.session import obter_sessao
from app.integracoes.caixa import ClienteCaixa, ErroFonteExterna
from app.models import Concurso
from app.schemas.concurso import ConcursoSaida
from app.schemas.importacao import ResumoAtualizacaoSaida
from app.services.atualizacao import atualizar_concursos

router = APIRouter(prefix="/concursos", tags=["concursos"])

LIMITE_PADRAO_POR_ATUALIZACAO = 300


class PaginaConcursos(BaseModel):
    total: int
    itens: list[ConcursoSaida]


@router.get("", response_model=PaginaConcursos)
def listar_concursos(
    limite: int = Query(20, ge=1, le=500, description="Quantos concursos devolver"),
    deslocamento: int = Query(0, ge=0, description="Quantos pular (para paginar)"),
    sessao: Session = Depends(obter_sessao),
) -> PaginaConcursos:
    """Lista os concursos do mais recente para o mais antigo."""
    total = sessao.scalar(select(func.count()).select_from(Concurso)) or 0
    itens = sessao.scalars(
        select(Concurso).order_by(Concurso.numero.desc()).limit(limite).offset(deslocamento)
    ).all()
    return PaginaConcursos(total=total, itens=[ConcursoSaida.model_validate(c) for c in itens])


@router.get("/{numero}", response_model=ConcursoSaida)
def consultar_concurso(numero: int, sessao: Session = Depends(obter_sessao)) -> ConcursoSaida:
    concurso = sessao.scalar(select(Concurso).where(Concurso.numero == numero))
    if concurso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Concurso {numero} não está no banco.")
    return ConcursoSaida.model_validate(concurso)


@router.post("/atualizar", response_model=ResumoAtualizacaoSaida)
def atualizar(
    limite: int = Query(
        LIMITE_PADRAO_POR_ATUALIZACAO,
        ge=1,
        le=5000,
        description="Máximo de concursos buscados nesta execução",
    ),
    sessao: Session = Depends(obter_sessao),
    cliente: ClienteCaixa = Depends(obter_cliente_caixa),
) -> ResumoAtualizacaoSaida:
    """Busca na API da Caixa os concursos que faltam no banco e grava.

    Pode ser executado quantas vezes quiser: concursos já gravados nunca são duplicados.
    """
    try:
        resumo = atualizar_concursos(sessao, cliente, limite=limite)
    except ErroFonteExterna as erro:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Não foi possível consultar a Caixa: {erro}"
        ) from None
    return ResumoAtualizacaoSaida(**asdict(resumo))
