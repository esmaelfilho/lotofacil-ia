"""Pares e trios de dezenas que mais saíram juntos (RF-03.13)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.estatisticas import Combinacao, CombinacoesSaida
from app.services.estatisticas.comum import CTE_JANELA, contar_concursos, percentual

_PARES = text(f"""
    WITH {CTE_JANELA}
    SELECT ARRAY[a.x, b.x] AS dezenas, count(*) AS vezes
    FROM janela c, unnest(c.dezenas) a(x), unnest(c.dezenas) b(x)
    WHERE a.x < b.x
    GROUP BY a.x, b.x
    ORDER BY vezes DESC, a.x, b.x
    LIMIT :quantidade
""")

_TRIOS = text(f"""
    WITH {CTE_JANELA}
    SELECT ARRAY[a.x, b.x, t.x] AS dezenas, count(*) AS vezes
    FROM janela c, unnest(c.dezenas) a(x), unnest(c.dezenas) b(x), unnest(c.dezenas) t(x)
    WHERE a.x < b.x AND b.x < t.x
    GROUP BY a.x, b.x, t.x
    ORDER BY vezes DESC, a.x, b.x, t.x
    LIMIT :quantidade
""")


def combinacoes(
    sessao: Session, tamanho: int = 2, quantidade: int = 20, ultimos: int | None = None
) -> CombinacoesSaida:
    if tamanho not in (2, 3):
        raise ValueError("o tamanho deve ser 2 (pares) ou 3 (trios)")
    consulta = _PARES if tamanho == 2 else _TRIOS
    concursos = contar_concursos(sessao, ultimos)
    linhas = sessao.execute(consulta, {"ultimos": ultimos, "quantidade": quantidade})
    return CombinacoesSaida(
        tamanho=tamanho,
        concursos=concursos,
        combinacoes=[
            Combinacao(
                dezenas=list(linha.dezenas),
                vezes=linha.vezes,
                percentual=percentual(linha.vezes, concursos),
            )
            for linha in linhas
        ],
    )
