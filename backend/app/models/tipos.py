"""Tipos e regras compartilhados pelos modelos."""

from sqlalchemy import SmallInteger
from sqlalchemy.dialects.postgresql import ARRAY

# Dezenas sempre em ordem crescente (ADR-002).
Dezenas = ARRAY(SmallInteger, dimensions=1)


def regra_dezenas(coluna: str, minimo: int, maximo: int) -> str:
    """Expressão SQL do CHECK que usa a função criada na migração inicial."""
    return f"lotofacil_dezenas_validas({coluna}, {minimo}, {maximo})"
