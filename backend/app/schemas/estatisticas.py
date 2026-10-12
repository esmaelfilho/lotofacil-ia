"""Respostas dos endpoints de estatística."""

from datetime import date

from pydantic import BaseModel


class FrequenciaDezena(BaseModel):
    dezena: int
    total: int
    percentual: float
    janelas: dict[int, int]


class FrequenciaSaida(BaseModel):
    concursos: int
    janelas: list[int]
    dezenas: list[FrequenciaDezena]


class DezenaVezes(BaseModel):
    dezena: int
    vezes: int


class QuentesFriasSaida(BaseModel):
    janela: int
    concursos_na_janela: int
    quentes: list[DezenaVezes]
    frias: list[DezenaVezes]


class AtrasoDezena(BaseModel):
    dezena: int
    atraso_atual: int
    maior_atraso: int
    ultimo_concurso: int | None


class AtrasosSaida(BaseModel):
    concursos: int
    dezenas: list[AtrasoDezena]


class PerfilSaida(BaseModel):
    pares: int
    impares: int
    primos: int
    soma: int
    moldura: int
    miolo: int
    por_linha: list[int]
    por_coluna: list[int]
    maior_sequencia: int
    blocos_consecutivos: int
    fibonacci: int
    multiplos_de_3: int


class PerfilConcurso(BaseModel):
    numero: int
    data_sorteio: date
    dezenas: list[int]
    perfil: PerfilSaida
    repetidas_do_anterior: int | None


class PaginaPerfis(BaseModel):
    total: int
    itens: list[PerfilConcurso]


class ValorDistribuicao(BaseModel):
    valor: int
    concursos: int
    percentual: float


class DistribuicaoSaida(BaseModel):
    caracteristica: str
    concursos: int
    media: float | None
    minimo: int | None
    maximo: int | None
    valores: list[ValorDistribuicao]


class FiltroDezenasSaida(BaseModel):
    obrigatorias: list[int]
    excluidas: list[int]
    concursos_analisados: int
    concursos_atendidos: int
    percentual: float
    ultimo_concurso_atendido: int | None


class Combinacao(BaseModel):
    dezenas: list[int]
    vezes: int
    percentual: float


class CombinacoesSaida(BaseModel):
    tamanho: int
    concursos: int
    combinacoes: list[Combinacao]
