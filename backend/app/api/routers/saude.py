"""Endpoint de saúde: informa se a API está no ar e se o banco responde."""

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from app.db.verificacao import ErroDeConexao, revisoes_do_banco, verificar_conexao

router = APIRouter(tags=["saúde"])


class Saude(BaseModel):
    status: str
    banco: str
    revisao_do_banco: str | None = None
    revisao_mais_recente: str | None = None
    detalhe: str | None = None


@router.get("/saude", response_model=Saude)
def saude(request: Request, response: Response) -> Saude:
    engine = request.app.state.engine
    try:
        verificar_conexao(engine)
    except ErroDeConexao as erro:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return Saude(status="erro", banco="indisponível", detalhe=str(erro))
    atual, mais_recente = revisoes_do_banco(engine)
    return Saude(
        status="ok" if atual == mais_recente else "migracoes_pendentes",
        banco="conectado",
        revisao_do_banco=atual,
        revisao_mais_recente=mais_recente,
    )
