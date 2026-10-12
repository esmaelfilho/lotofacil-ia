"""Entradas e respostas de regras, estratégias, gerações e conferências."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.concurso import normalizar_dezenas
from app.schemas.estatisticas import PerfilSaida


class RegraSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    descricao: str | None
    parametros_padrao: dict[str, int]
    ativa: bool


class FaixaEntrada(BaseModel):
    codigo: str
    minimo: int
    maximo: int


class FaixaSaida(FaixaEntrada):
    nome: str


class EstrategiaEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str | None = None
    regras: list[FaixaEntrada] = Field(default_factory=list)

    @field_validator("nome")
    @classmethod
    def _sem_espacos_nas_pontas(cls, nome: str) -> str:
        nome = nome.strip()
        if not nome:
            raise ValueError("o nome não pode ficar vazio")
        return nome


class EstrategiaSaida(BaseModel):
    id: int
    nome: str
    descricao: str | None
    ativa: bool
    criada_em: datetime
    atualizada_em: datetime
    usada: bool
    regras: list[FaixaSaida]


class GeracaoEntrada(BaseModel):
    estrategia_id: int | None = None
    quantidade: int = Field(5, ge=1, le=100)
    dezenas_por_jogo: int = Field(15, ge=15, le=20)
    obrigatorias: list[int] = Field(default_factory=list)
    excluidas: list[int] = Field(default_factory=list)
    concurso_base: int | None = Field(None, description="Padrão: o último concurso do banco")
    semente: int | None = Field(None, ge=0, le=2**53, description="Padrão: sorteada")

    @field_validator("obrigatorias")
    @classmethod
    def _obrigatorias(cls, dezenas: list[int]) -> list[int]:
        return normalizar_dezenas(dezenas, 0, 20)

    @field_validator("excluidas")
    @classmethod
    def _excluidas(cls, dezenas: list[int]) -> list[int]:
        return normalizar_dezenas(dezenas, 0, 10)


class JogoSaida(BaseModel):
    id: int
    sequencia: int
    dezenas: list[int]
    perfil: PerfilSaida
    repetidas_do_concurso_base: int


class GeracaoResumo(BaseModel):
    id: int
    criada_em: datetime
    estrategia_id: int | None
    estrategia_nome: str | None
    concurso_base: int
    quantidade_jogos: int
    dezenas_por_jogo: int
    obrigatorias: list[int]
    excluidas: list[int]
    regras: list[FaixaSaida]
    semente: int | None


class GeracaoSaida(GeracaoResumo):
    tentativas: int | None = None
    jogos: list[JogoSaida]


class JogoConferido(BaseModel):
    jogo_id: int
    sequencia: int
    dezenas: list[int]
    acertos: int
    dezenas_acertadas: list[int]


class ConferenciaSaida(BaseModel):
    geracao_id: int
    concurso: int
    dezenas_sorteadas: list[int]
    jogos: list[JogoConferido]
    por_acertos: dict[int, int]


class ConferirHistoricoEntrada(BaseModel):
    dezenas: list[int]

    @field_validator("dezenas")
    @classmethod
    def _dezenas(cls, dezenas: list[int]) -> list[int]:
        return normalizar_dezenas(dezenas, 15, 20)


class ConferenciaHistoricoSaida(BaseModel):
    dezenas: list[int]
    concursos: int
    por_acertos: dict[int, int]
    maior_acerto: int | None
    ultimo_concurso_com_11_ou_mais: int | None
