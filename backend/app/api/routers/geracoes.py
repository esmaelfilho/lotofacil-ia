"""Geração e conferência de jogos (RF-05, RF-06).

Gerar jogos com filtros estatísticos não aumenta a chance de acerto: cada combinação tem a
mesma chance em todo sorteio.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.erros import http
from app.db.session import obter_sessao
from app.schemas.jogos import (
    ConferenciaHistoricoSaida,
    ConferenciaSaida,
    ConferirHistoricoEntrada,
    GeracaoEntrada,
    GeracaoResumo,
    GeracaoSaida,
)
from app.services import avaliacao, geracao
from app.services.erros import ErroDeNegocio

router = APIRouter(tags=["jogos"])


class PaginaGeracoes(BaseModel):
    total: int
    itens: list[GeracaoResumo]


@router.post("/geracoes", response_model=GeracaoSaida, status_code=201)
def gerar_jogos(entrada: GeracaoEntrada, sessao: Session = Depends(obter_sessao)) -> GeracaoSaida:
    """Gera jogos que respeitam a estratégia, as obrigatórias e as excluídas.

    Informe a mesma `semente` e os mesmos parâmetros para obter exatamente os mesmos jogos."""
    try:
        return geracao.gerar(sessao, entrada)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.get("/geracoes", response_model=PaginaGeracoes)
def listar_geracoes(
    limite: int = Query(20, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
    sessao: Session = Depends(obter_sessao),
) -> PaginaGeracoes:
    """As gerações mais recentes primeiro (sem os jogos)."""
    total, itens = geracao.listar(sessao, limite, deslocamento)
    return PaginaGeracoes(total=total, itens=itens)


@router.get("/geracoes/{geracao_id}", response_model=GeracaoSaida)
def obter_geracao(geracao_id: int, sessao: Session = Depends(obter_sessao)) -> GeracaoSaida:
    try:
        return geracao.obter(sessao, geracao_id)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.post("/geracoes/{geracao_id}/conferir", response_model=ConferenciaSaida)
def conferir_geracao(
    geracao_id: int,
    concurso: int = Query(..., ge=1, description="Número do concurso"),
    sessao: Session = Depends(obter_sessao),
) -> ConferenciaSaida:
    """Confere todos os jogos da geração contra um concurso e grava os acertos."""
    try:
        return avaliacao.conferir_geracao(sessao, geracao_id, concurso)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.post("/jogos/conferir-historico", response_model=ConferenciaHistoricoSaida)
def conferir_historico(
    entrada: ConferirHistoricoEntrada, sessao: Session = Depends(obter_sessao)
) -> ConferenciaHistoricoSaida:
    """Quantas vezes um jogo (15 a 20 dezenas) teria feito 11, 12, 13, 14 e 15 pontos."""
    return avaliacao.conferir_historico(sessao, entrada.dezenas)
