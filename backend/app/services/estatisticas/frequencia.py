"""Frequência das dezenas (RF-03.1) e dezenas quentes e frias (RF-03.2)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.estatisticas import (
    DezenaVezes,
    FrequenciaDezena,
    FrequenciaSaida,
    QuentesFriasSaida,
)
from app.services.estatisticas.comum import DEZENAS, contar_concursos, percentual

JANELAS_PADRAO = (10, 50, 100)


def frequencia(sessao: Session, janelas: tuple[int, ...] = JANELAS_PADRAO) -> FrequenciaSaida:
    """Quantas vezes cada dezena saiu no total e nos últimos N concursos de cada janela."""
    janelas = tuple(sorted(set(janelas)))
    filtros = "".join(
        f", count(*) FILTER (WHERE pos <= :j{i}) AS j{i}" for i in range(len(janelas))
    )
    consulta = text(f"""
        WITH ordenados AS (
          SELECT dezenas, row_number() OVER (ORDER BY numero DESC) AS pos FROM concursos
        )
        SELECT d AS dezena, count(*) AS total{filtros}
        FROM ordenados, unnest(dezenas) AS d
        GROUP BY d
    """)
    parametros = {f"j{i}": j for i, j in enumerate(janelas)}
    linhas = {linha.dezena: linha for linha in sessao.execute(consulta, parametros)}
    concursos = contar_concursos(sessao)

    dezenas = []
    for d in DEZENAS:
        linha = linhas.get(d)
        total = linha.total if linha else 0
        por_janela = {j: (getattr(linha, f"j{i}") if linha else 0) for i, j in enumerate(janelas)}
        dezenas.append(
            FrequenciaDezena(
                dezena=d, total=total, percentual=percentual(total, concursos), janelas=por_janela
            )
        )
    return FrequenciaSaida(concursos=concursos, janelas=list(janelas), dezenas=dezenas)


def quentes_e_frias(sessao: Session, janela: int = 50, quantidade: int = 5) -> QuentesFriasSaida:
    """As dezenas que mais e menos saíram nos últimos `janela` concursos.

    Empates são desfeitos pelo número da dezena (a menor vem primeiro).
    """
    resultado = frequencia(sessao, (janela,))
    vezes = [DezenaVezes(dezena=f.dezena, vezes=f.janelas[janela]) for f in resultado.dezenas]
    return QuentesFriasSaida(
        janela=janela,
        concursos_na_janela=min(janela, resultado.concursos),
        quentes=sorted(vezes, key=lambda v: (-v.vezes, v.dezena))[:quantidade],
        frias=sorted(vezes, key=lambda v: (v.vezes, v.dezena))[:quantidade],
    )
