"""Carga do catálogo de regras estatísticas (só dados; nenhuma tabela nova).

Cada regra é uma faixa (mínimo e máximo) sobre uma característica do jogo, com as mesmas
definições de app/services/estatisticas/perfil.py. As faixas padrão cobrem cerca de 60% a
80% dos resultados possíveis. Os dados ficam escritos aqui (e não importados do código da
aplicação) para que a migração continue igual mesmo se o código mudar.

Revisão: 0003
Anterior: 0002
Criada em: 2026-10-12
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REGRAS = [
    ("pares", "Pares", "Quantidade de dezenas pares no jogo.", 7, 8),
    ("primos", "Primos", "Dezenas primas: 02 03 05 07 11 13 17 19 23.", 4, 6),
    ("soma", "Soma das dezenas", "Soma de todas as dezenas do jogo.", 180, 220),
    ("moldura", "Moldura", "Dezenas da borda do volante 5×5 (16 dezenas).", 9, 11),
    ("miolo", "Miolo", "Dezenas do centro do volante: 07 08 09 12 13 14 17 18 19.", 4, 6),
    (
        "maior_sequencia",
        "Maior sequência",
        "Tamanho do maior trecho de dezenas consecutivas (ex.: 04 05 06 = 3).",
        3,
        5,
    ),
    ("fibonacci", "Fibonacci", "Dezenas da sequência de Fibonacci: 01 02 03 05 08 13 21.", 3, 5),
    ("multiplos_de_3", "Múltiplos de 3", "Dezenas 03 06 09 12 15 18 21 24.", 4, 6),
    (
        "repetidas_do_concurso_base",
        "Repetidas do concurso base",
        "Quantas dezenas do jogo saíram no concurso base da geração.",
        8,
        10,
    ),
]


def upgrade() -> None:
    for codigo, nome, descricao, minimo, maximo in REGRAS:
        op.execute(
            sa.text(
                "INSERT INTO regras_estatisticas (codigo, nome, descricao, parametros_padrao) "
                "VALUES (:codigo, :nome, :descricao, CAST(:parametros AS jsonb)) "
                "ON CONFLICT (codigo) DO NOTHING"
            ).bindparams(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
                parametros=json.dumps({"minimo": minimo, "maximo": maximo}),
            )
        )


def downgrade() -> None:
    # Falha (RESTRICT) se alguma estratégia ainda usa uma dessas regras: de propósito.
    op.execute(
        sa.text("DELETE FROM regras_estatisticas WHERE codigo IN :codigos").bindparams(
            sa.bindparam("codigos", [r[0] for r in REGRAS], expanding=True)
        )
    )
