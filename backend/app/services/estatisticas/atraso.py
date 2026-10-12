"""Atraso atual e maior atraso de cada dezena (RF-03.3).

O atraso conta concursos que existem no banco, pela posição em ordem de número
(row_number), e não pela diferença entre números: uma lacuna na numeração não aumenta o
atraso. Atraso 0 = a dezena saiu no último concurso. Uma dezena que nunca saiu tem atraso
igual ao total de concursos.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.estatisticas import AtrasoDezena, AtrasosSaida
from app.services.estatisticas.comum import DEZENAS, contar_concursos

CONSULTA = text("""
    WITH c AS (
      SELECT numero, dezenas, row_number() OVER (ORDER BY numero) AS seq FROM concursos
    ),
    ap AS (
      SELECT d, seq, numero,
             seq - coalesce(lag(seq) OVER (PARTITION BY d ORDER BY seq), 0) - 1 AS intervalo
      FROM c, unnest(dezenas) AS d
    )
    SELECT d AS dezena, max(seq) AS ultima_posicao, max(intervalo) AS maior_intervalo,
           max(numero) AS ultimo_concurso
    FROM ap GROUP BY d
""")


def atrasos(sessao: Session) -> AtrasosSaida:
    concursos = contar_concursos(sessao)
    linhas = {linha.dezena: linha for linha in sessao.execute(CONSULTA)}
    dezenas = []
    for d in DEZENAS:
        linha = linhas.get(d)
        if linha is None:
            dezenas.append(
                AtrasoDezena(
                    dezena=d, atraso_atual=concursos, maior_atraso=concursos, ultimo_concurso=None
                )
            )
            continue
        atual = concursos - linha.ultima_posicao
        dezenas.append(
            AtrasoDezena(
                dezena=d,
                atraso_atual=atual,
                maior_atraso=max(linha.maior_intervalo, atual),
                ultimo_concurso=linha.ultimo_concurso,
            )
        )
    return AtrasosSaida(concursos=concursos, dezenas=dezenas)
