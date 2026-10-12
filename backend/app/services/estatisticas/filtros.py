"""Dezenas obrigatórias e excluídas (RF-03.9).

Em quantos concursos todas as obrigatórias saíram e nenhuma excluída saiu.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.concurso import normalizar_dezenas
from app.schemas.estatisticas import FiltroDezenasSaida
from app.services.estatisticas.comum import CTE_JANELA, contar_concursos, percentual

MAXIMO_OBRIGATORIAS = 15
MAXIMO_EXCLUIDAS = 10  # excluir mais de 10 deixaria menos de 15 dezenas possíveis

CONSULTA = text(f"""
    WITH {CTE_JANELA}
    SELECT count(*) AS atendidos, max(numero) AS ultimo
    FROM janela
    WHERE dezenas @> CAST(:obrigatorias AS smallint[])
      AND NOT dezenas && CAST(:excluidas AS smallint[])
""")


def validar_filtro(obrigatorias: list[int], excluidas: list[int]) -> tuple[list[int], list[int]]:
    """Valida e ordena as listas. Lança ValueError com mensagem em português."""
    if not obrigatorias and not excluidas:
        raise ValueError("informe ao menos uma dezena obrigatória ou excluída")
    try:
        obrigatorias = normalizar_dezenas(obrigatorias, 0, MAXIMO_OBRIGATORIAS)
    except ValueError as erro:
        raise ValueError(f"obrigatórias: {erro}") from None
    try:
        excluidas = normalizar_dezenas(excluidas, 0, MAXIMO_EXCLUIDAS)
    except ValueError as erro:
        raise ValueError(f"excluídas: {erro}") from None
    em_comum = sorted(set(obrigatorias) & set(excluidas))
    if em_comum:
        raise ValueError(
            "uma dezena não pode ser obrigatória e excluída ao mesmo tempo: "
            + ", ".join(f"{d:02d}" for d in em_comum)
        )
    return obrigatorias, excluidas


def filtrar_dezenas(
    sessao: Session,
    obrigatorias: list[int],
    excluidas: list[int],
    ultimos: int | None = None,
) -> FiltroDezenasSaida:
    obrigatorias, excluidas = validar_filtro(obrigatorias, excluidas)
    linha = sessao.execute(
        CONSULTA, {"ultimos": ultimos, "obrigatorias": obrigatorias, "excluidas": excluidas}
    ).one()
    analisados = contar_concursos(sessao, ultimos)
    return FiltroDezenasSaida(
        obrigatorias=obrigatorias,
        excluidas=excluidas,
        concursos_analisados=analisados,
        concursos_atendidos=linha.atendidos,
        percentual=percentual(linha.atendidos, analisados),
        ultimo_concurso_atendido=linha.ultimo,
    )
