"""Catálogo de regras e estratégias (RF-04)."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.erros import http
from app.db.session import obter_sessao
from app.schemas.jogos import EstrategiaEntrada, EstrategiaSaida, RegraSaida
from app.services import estrategias
from app.services.erros import ErroDeNegocio

router = APIRouter(tags=["estratégias"])


@router.get("/regras", response_model=list[RegraSaida])
def listar_regras(sessao: Session = Depends(obter_sessao)) -> list[RegraSaida]:
    """Regras que podem ser usadas nas estratégias, com a faixa padrão de cada uma."""
    return estrategias.listar_regras(sessao)


@router.get("/estrategias", response_model=list[EstrategiaSaida])
def listar_estrategias(
    incluir_inativas: bool = Query(True), sessao: Session = Depends(obter_sessao)
) -> list[EstrategiaSaida]:
    return estrategias.listar(sessao, incluir_inativas)


@router.post("/estrategias", response_model=EstrategiaSaida, status_code=201)
def criar_estrategia(
    entrada: EstrategiaEntrada, sessao: Session = Depends(obter_sessao)
) -> EstrategiaSaida:
    """Cria uma estratégia. Cada regra recebe um mínimo e um máximo."""
    try:
        return estrategias.criar(sessao, entrada)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.get("/estrategias/{estrategia_id}", response_model=EstrategiaSaida)
def obter_estrategia(
    estrategia_id: int, sessao: Session = Depends(obter_sessao)
) -> EstrategiaSaida:
    try:
        return estrategias.obter(sessao, estrategia_id)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.put("/estrategias/{estrategia_id}", response_model=EstrategiaSaida)
def atualizar_estrategia(
    estrategia_id: int, entrada: EstrategiaEntrada, sessao: Session = Depends(obter_sessao)
) -> EstrategiaSaida:
    """Altera nome, descrição e regras. As gerações já feitas guardam a versão antiga."""
    try:
        return estrategias.atualizar(sessao, estrategia_id, entrada)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.post("/estrategias/{estrategia_id}/desativar", response_model=EstrategiaSaida)
def desativar_estrategia(
    estrategia_id: int, sessao: Session = Depends(obter_sessao)
) -> EstrategiaSaida:
    try:
        return estrategias.alterar_ativa(sessao, estrategia_id, False)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.post("/estrategias/{estrategia_id}/ativar", response_model=EstrategiaSaida)
def ativar_estrategia(
    estrategia_id: int, sessao: Session = Depends(obter_sessao)
) -> EstrategiaSaida:
    try:
        return estrategias.alterar_ativa(sessao, estrategia_id, True)
    except ErroDeNegocio as erro:
        raise http(erro) from None


@router.delete("/estrategias/{estrategia_id}", status_code=204)
def excluir_estrategia(estrategia_id: int, sessao: Session = Depends(obter_sessao)) -> Response:
    """Exclui só estratégias nunca usadas. As já usadas devem ser desativadas."""
    try:
        estrategias.excluir(sessao, estrategia_id)
    except ErroDeNegocio as erro:
        raise http(erro) from None
    return Response(status_code=204)
