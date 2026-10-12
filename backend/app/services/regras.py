"""Regras estatísticas usadas como filtro dos jogos (RF-04.1).

Cada regra é uma faixa (mínimo e máximo, inclusive) sobre um valor calculado do jogo. Os
valores usam as definições de estatisticas/perfil.py, as mesmas das estatísticas. O
catálogo com nomes e faixas padrão fica na tabela regras_estatisticas (migração 0003).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.services.erros import ErroDeNegocio
from app.services.estatisticas.perfil import Perfil, calcular_perfil, repetidas

Calculo = Callable[[Perfil, Sequence[int], Sequence[int]], int]

# código -> (cálculo do valor, menor e maior valor aceitos numa faixa)
CALCULOS: dict[str, tuple[Calculo, int, int]] = {
    "pares": (lambda p, _j, _b: p.pares, 0, 20),
    "primos": (lambda p, _j, _b: p.primos, 0, 9),
    "soma": (lambda p, _j, _b: p.soma, 0, 400),
    "moldura": (lambda p, _j, _b: p.moldura, 0, 16),
    "miolo": (lambda p, _j, _b: p.miolo, 0, 9),
    "maior_sequencia": (lambda p, _j, _b: p.maior_sequencia, 0, 20),
    "fibonacci": (lambda p, _j, _b: p.fibonacci, 0, 7),
    "multiplos_de_3": (lambda p, _j, _b: p.multiplos_de_3, 0, 8),
    "repetidas_do_concurso_base": (lambda _p, j, b: repetidas(j, b), 0, 15),
}


@dataclass(frozen=True)
class Faixa:
    codigo: str
    minimo: int
    maximo: int

    def como_dict(self) -> dict[str, int | str]:
        return {"codigo": self.codigo, "minimo": self.minimo, "maximo": self.maximo}


def validar_faixa(codigo: str, minimo: int, maximo: int) -> Faixa:
    if codigo not in CALCULOS:
        raise ErroDeNegocio(f"regra desconhecida: {codigo}")
    _, menor, maior = CALCULOS[codigo]
    if minimo > maximo:
        raise ErroDeNegocio(f"{codigo}: o mínimo ({minimo}) é maior que o máximo ({maximo})")
    if minimo < menor or maximo > maior:
        raise ErroDeNegocio(f"{codigo}: a faixa deve ficar entre {menor} e {maior}")
    return Faixa(codigo, minimo, maximo)


def valor(codigo: str, perfil: Perfil, jogo: Sequence[int], base: Sequence[int]) -> int:
    return CALCULOS[codigo][0](perfil, jogo, base)


def atende(jogo: Sequence[int], faixas: Sequence[Faixa], base: Sequence[int]) -> bool:
    """True se o jogo fica dentro de todas as faixas."""
    if not faixas:
        return True
    perfil = calcular_perfil(jogo)
    return all(f.minimo <= valor(f.codigo, perfil, jogo, base) <= f.maximo for f in faixas)
