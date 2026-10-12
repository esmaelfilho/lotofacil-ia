"""Perfil de cada concurso e distribuição das características (RF-03.4 a 03.8, 03.10 a 03.12).

O perfil é calculado em Python (perfil.py) a partir das dezenas lidas do banco, para que a
mesma definição sirva aos concursos e aos jogos gerados. "Concurso anterior" é o concurso
anterior que existe no banco (se houver lacuna na numeração, é o último antes dela).
"""

from collections import Counter
from dataclasses import asdict
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Concurso
from app.schemas.estatisticas import (
    DistribuicaoSaida,
    PaginaPerfis,
    PerfilConcurso,
    PerfilSaida,
    ValorDistribuicao,
)
from app.services.estatisticas.comum import contar_concursos, percentual
from app.services.estatisticas.perfil import Perfil, calcular_perfil, repetidas


class Caracteristica(StrEnum):
    pares = "pares"
    impares = "impares"
    primos = "primos"
    soma = "soma"
    moldura = "moldura"
    miolo = "miolo"
    linha_1 = "linha_1"
    linha_2 = "linha_2"
    linha_3 = "linha_3"
    linha_4 = "linha_4"
    linha_5 = "linha_5"
    coluna_1 = "coluna_1"
    coluna_2 = "coluna_2"
    coluna_3 = "coluna_3"
    coluna_4 = "coluna_4"
    coluna_5 = "coluna_5"
    maior_sequencia = "maior_sequencia"
    blocos_consecutivos = "blocos_consecutivos"
    fibonacci = "fibonacci"
    multiplos_de_3 = "multiplos_de_3"
    repetidas_do_anterior = "repetidas_do_anterior"


def _valor(caracteristica: Caracteristica, perfil: Perfil, repetidas_: int | None) -> int | None:
    nome = caracteristica.value
    if nome == "repetidas_do_anterior":
        return repetidas_
    if nome.startswith("linha_"):
        return perfil.por_linha[int(nome[-1]) - 1]
    if nome.startswith("coluna_"):
        return perfil.por_coluna[int(nome[-1]) - 1]
    return getattr(perfil, nome)


def _perfil_saida(perfil: Perfil) -> PerfilSaida:
    return PerfilSaida(**asdict(perfil))


def perfis(sessao: Session, limite: int = 20, deslocamento: int = 0) -> PaginaPerfis:
    """Perfil dos concursos, do mais recente para o mais antigo, com paginação."""
    linhas = sessao.execute(
        select(Concurso.numero, Concurso.data_sorteio, Concurso.dezenas)
        .order_by(Concurso.numero.desc())
        .limit(limite + 1)  # +1 para saber o concurso anterior ao último da página
        .offset(deslocamento)
    ).all()
    itens = []
    for i, linha in enumerate(linhas[:limite]):
        anterior = linhas[i + 1] if i + 1 < len(linhas) else None
        itens.append(
            PerfilConcurso(
                numero=linha.numero,
                data_sorteio=linha.data_sorteio,
                dezenas=list(linha.dezenas),
                perfil=_perfil_saida(calcular_perfil(linha.dezenas)),
                repetidas_do_anterior=(
                    repetidas(linha.dezenas, anterior.dezenas) if anterior else None
                ),
            )
        )
    return PaginaPerfis(total=contar_concursos(sessao), itens=itens)


def distribuicao(
    sessao: Session, caracteristica: Caracteristica, ultimos: int | None = None
) -> DistribuicaoSaida:
    """Em quantos concursos cada valor da característica aconteceu."""
    consulta = select(Concurso.dezenas).order_by(Concurso.numero.desc())
    if ultimos is not None:
        consulta = consulta.limit(ultimos + 1)  # +1 para a repetição do mais antigo
    todas = sessao.scalars(consulta).all()
    analisadas = todas if ultimos is None else todas[:ultimos]

    contagem: Counter[int] = Counter()
    for i, dezenas in enumerate(analisadas):
        anterior = todas[i + 1] if i + 1 < len(todas) else None
        rep = repetidas(dezenas, anterior) if anterior is not None else None
        valor = _valor(caracteristica, calcular_perfil(dezenas), rep)
        if valor is not None:
            contagem[valor] += 1

    total = sum(contagem.values())
    soma = sum(valor * vezes for valor, vezes in contagem.items())
    return DistribuicaoSaida(
        caracteristica=caracteristica.value,
        concursos=total,
        media=round(soma / total, 2) if total else None,
        minimo=min(contagem) if contagem else None,
        maximo=max(contagem) if contagem else None,
        valores=[
            ValorDistribuicao(valor=v, concursos=n, percentual=percentual(n, total))
            for v, n in sorted(contagem.items())
        ],
    )
