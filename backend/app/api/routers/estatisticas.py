"""Endpoints de estatística. Só consultam o banco; nada é gravado.

Cada sorteio é independente: as estatísticas descrevem o passado e não aumentam a chance de
acerto.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import obter_sessao
from app.schemas.estatisticas import (
    AtrasosSaida,
    CombinacoesSaida,
    DistribuicaoSaida,
    FiltroDezenasSaida,
    FrequenciaSaida,
    PaginaPerfis,
    QuentesFriasSaida,
)
from app.services.estatisticas.atraso import atrasos
from app.services.estatisticas.combinacoes import combinacoes
from app.services.estatisticas.distribuicao import Caracteristica, distribuicao, perfis
from app.services.estatisticas.filtros import filtrar_dezenas
from app.services.estatisticas.frequencia import JANELAS_PADRAO, frequencia, quentes_e_frias

router = APIRouter(prefix="/estatisticas", tags=["estatísticas"])

MAXIMO_DE_CONCURSOS = 10_000

ULTIMOS = Query(
    None,
    ge=1,
    le=MAXIMO_DE_CONCURSOS,
    description="Considerar só os últimos N concursos (vazio = todos)",
)


@router.get("/frequencia", response_model=FrequenciaSaida)
def obter_frequencia(
    janelas: list[int] = Query(
        list(JANELAS_PADRAO),
        description="Janelas em número de concursos (ex.: 10, 50, 100)",
    ),
    sessao: Session = Depends(obter_sessao),
) -> FrequenciaSaida:
    """Quantas vezes cada dezena saiu: no total e nos últimos N concursos de cada janela."""
    if not 1 <= len(janelas) <= 5 or any(not 1 <= j <= MAXIMO_DE_CONCURSOS for j in janelas):
        raise HTTPException(
            422,
            f"Informe de 1 a 5 janelas, cada uma entre 1 e {MAXIMO_DE_CONCURSOS}.",
        )
    return frequencia(sessao, tuple(janelas))


@router.get("/quentes-frias", response_model=QuentesFriasSaida)
def obter_quentes_e_frias(
    janela: int = Query(50, ge=1, le=MAXIMO_DE_CONCURSOS, description="Últimos N concursos"),
    quantidade: int = Query(5, ge=1, le=25, description="Quantas dezenas em cada lista"),
    sessao: Session = Depends(obter_sessao),
) -> QuentesFriasSaida:
    """As dezenas que mais saíram (quentes) e as que menos saíram (frias) na janela."""
    return quentes_e_frias(sessao, janela, quantidade)


@router.get("/atrasos", response_model=AtrasosSaida)
def obter_atrasos(sessao: Session = Depends(obter_sessao)) -> AtrasosSaida:
    """Há quantos concursos cada dezena não sai, e o maior atraso que ela já teve."""
    return atrasos(sessao)


@router.get("/perfil", response_model=PaginaPerfis)
def obter_perfis(
    limite: int = Query(20, ge=1, le=500, description="Quantos concursos devolver"),
    deslocamento: int = Query(0, ge=0, description="Quantos pular (para paginar)"),
    sessao: Session = Depends(obter_sessao),
) -> PaginaPerfis:
    """Perfil de cada concurso, do mais recente para o mais antigo: pares/ímpares, primos,
    soma, moldura/miolo, linhas e colunas, sequências, Fibonacci, múltiplos de 3 e
    dezenas repetidas do concurso anterior."""
    return perfis(sessao, limite, deslocamento)


@router.get("/distribuicao", response_model=DistribuicaoSaida)
def obter_distribuicao(
    caracteristica: Caracteristica = Query(Caracteristica.pares),
    ultimos: int | None = ULTIMOS,
    sessao: Session = Depends(obter_sessao),
) -> DistribuicaoSaida:
    """Em quantos concursos cada valor de uma característica aconteceu.

    Exemplo: com `pares`, mostra em quantos concursos saíram 6 pares, 7 pares etc."""
    return distribuicao(sessao, caracteristica, ultimos)


@router.get("/obrigatorias-excluidas", response_model=FiltroDezenasSaida)
def obter_obrigatorias_excluidas(
    obrigatorias: list[int] = Query([], description="Dezenas que precisam ter saído"),
    excluidas: list[int] = Query([], description="Dezenas que não podem ter saído"),
    ultimos: int | None = ULTIMOS,
    sessao: Session = Depends(obter_sessao),
) -> FiltroDezenasSaida:
    """Em quantos concursos todas as obrigatórias saíram e nenhuma excluída saiu."""
    try:
        return filtrar_dezenas(sessao, obrigatorias, excluidas, ultimos)
    except ValueError as erro:
        raise HTTPException(422, str(erro)) from None


@router.get("/combinacoes", response_model=CombinacoesSaida)
def obter_combinacoes(
    tamanho: int = Query(2, ge=2, le=3, description="2 = pares de dezenas, 3 = trios"),
    quantidade: int = Query(20, ge=1, le=100, description="Quantas combinações devolver"),
    ultimos: int | None = ULTIMOS,
    sessao: Session = Depends(obter_sessao),
) -> CombinacoesSaida:
    """Pares ou trios de dezenas que mais saíram juntos."""
    return combinacoes(sessao, tamanho, quantidade, ultimos)
