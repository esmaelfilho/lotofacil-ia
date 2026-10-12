"""Perfil de uma lista de dezenas: pares, primos, soma, moldura/miolo, linhas, colunas...

Funções Python puras, sem banco. São usadas para o perfil dos concursos e serão usadas na
geração de jogos (Fase 4), para que cada característica tenha uma única definição.

Volante 5×5: linha = (d-1)//5 + 1, coluna = (d-1)%5 + 1.
"""

from collections.abc import Sequence
from dataclasses import dataclass

PRIMOS = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23})
MIOLO = frozenset({7, 8, 9, 12, 13, 14, 17, 18, 19})
FIBONACCI = frozenset({1, 2, 3, 5, 8, 13, 21})
MULTIPLOS_DE_3 = frozenset({3, 6, 9, 12, 15, 18, 21, 24})


@dataclass(frozen=True)
class Perfil:
    pares: int
    impares: int
    primos: int
    soma: int
    moldura: int
    miolo: int
    por_linha: tuple[int, int, int, int, int]
    por_coluna: tuple[int, int, int, int, int]
    maior_sequencia: int
    blocos_consecutivos: int
    fibonacci: int
    multiplos_de_3: int


def linha(dezena: int) -> int:
    return (dezena - 1) // 5 + 1


def coluna(dezena: int) -> int:
    return (dezena - 1) % 5 + 1


def sequencias(dezenas: Sequence[int]) -> list[int]:
    """Tamanhos dos trechos de dezenas consecutivas. Ex.: 1,2,3,5,6,8 -> [3, 2, 1]."""
    tamanhos: list[int] = []
    anterior: int | None = None
    for d in sorted(dezenas):
        if anterior is not None and d == anterior + 1:
            tamanhos[-1] += 1
        else:
            tamanhos.append(1)
        anterior = d
    return tamanhos


def calcular_perfil(dezenas: Sequence[int]) -> Perfil:
    pares = sum(1 for d in dezenas if d % 2 == 0)
    miolo = sum(1 for d in dezenas if d in MIOLO)
    por_linha = [0] * 5
    por_coluna = [0] * 5
    for d in dezenas:
        por_linha[linha(d) - 1] += 1
        por_coluna[coluna(d) - 1] += 1
    trechos = sequencias(dezenas)
    return Perfil(
        pares=pares,
        impares=len(dezenas) - pares,
        primos=sum(1 for d in dezenas if d in PRIMOS),
        soma=sum(dezenas),
        moldura=len(dezenas) - miolo,
        miolo=miolo,
        por_linha=tuple(por_linha),  # type: ignore[arg-type]
        por_coluna=tuple(por_coluna),  # type: ignore[arg-type]
        maior_sequencia=max(trechos, default=0),
        blocos_consecutivos=sum(1 for t in trechos if t >= 2),
        fibonacci=sum(1 for d in dezenas if d in FIBONACCI),
        multiplos_de_3=sum(1 for d in dezenas if d in MULTIPLOS_DE_3),
    )


def repetidas(dezenas: Sequence[int], anteriores: Sequence[int]) -> int:
    """Quantas dezenas também saíram no concurso anterior."""
    return len(set(dezenas) & set(anteriores))
