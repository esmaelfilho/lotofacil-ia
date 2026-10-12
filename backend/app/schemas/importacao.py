from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImportacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origem: str
    referencia: str
    status: str
    total_lidos: int
    total_inseridos: int
    total_ignorados: int
    total_rejeitados: int
    mensagem_erro: str | None
    iniciada_em: datetime
    finalizada_em: datetime | None


class ResumoAtualizacaoSaida(BaseModel):
    importacao_id: int
    status: str
    ultimo_concurso_caixa: int
    ultimo_concurso_banco: int | None
    buscados: int
    inseridos: int
    ignorados: int
    rejeitados: int
    faltam: int
    mensagem: str
