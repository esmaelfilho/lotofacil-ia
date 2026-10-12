"""Aumenta historico_importacoes.status para 30 caracteres.

A situação "CONCLUIDA_COM_REJEICOES" tem 23 caracteres e não cabia em varchar(20).
O erro apareceu no teste de atualização com concursos rejeitados.

Revisão: 0002
Anterior: 0001
Criada em: 2026-10-12
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "historico_importacoes",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
        existing_server_default="EM_ANDAMENTO",
    )


def downgrade() -> None:
    op.alter_column(
        "historico_importacoes",
        "status",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
        existing_server_default="EM_ANDAMENTO",
    )
