"""Geração de jogos (RF-05).

Sorteia combinações aleatórias e guarda só as que respeitam as dezenas obrigatórias e
excluídas e todas as faixas da estratégia, sem repetir jogo. O sorteio usa
random.Random(semente): com a mesma semente e os mesmos parâmetros, saem os mesmos jogos.
A geração guarda uma cópia das regras usadas, para não depender de mudanças posteriores
na estratégia.
"""

import random
from dataclasses import asdict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Concurso, Estrategia, GeracaoJogos, JogoGerado
from app.schemas.estatisticas import PerfilSaida
from app.schemas.jogos import (
    FaixaSaida,
    GeracaoEntrada,
    GeracaoResumo,
    GeracaoSaida,
    JogoSaida,
)
from app.services.erros import Conflito, ErroDeNegocio, NaoEncontrado
from app.services.estatisticas.perfil import calcular_perfil, repetidas
from app.services.estrategias import faixas_da_estrategia
from app.services.regras import Faixa, atende

MAXIMO_DE_TENTATIVAS = 100_000
MAIOR_SEMENTE = 2**53  # cabe em bigint e em número do JavaScript sem perder precisão


def sortear_jogos(
    quantidade: int,
    dezenas_por_jogo: int,
    obrigatorias: list[int],
    excluidas: list[int],
    faixas: list[Faixa],
    base: list[int],
    semente: int,
    maximo_de_tentativas: int = MAXIMO_DE_TENTATIVAS,
) -> tuple[list[list[int]], int]:
    """Devolve (jogos encontrados, tentativas usadas). Função pura, sem banco."""
    gerador = random.Random(semente)
    livres = [d for d in range(1, 26) if d not in obrigatorias and d not in excluidas]
    faltam = dezenas_por_jogo - len(obrigatorias)
    vistos: set[tuple[int, ...]] = set()
    jogos: list[list[int]] = []
    tentativas = 0
    while len(jogos) < quantidade and tentativas < maximo_de_tentativas:
        tentativas += 1
        jogo = sorted(obrigatorias + gerador.sample(livres, faltam))
        chave = tuple(jogo)
        if chave in vistos:
            continue
        vistos.add(chave)
        if atende(jogo, faixas, base):
            jogos.append(jogo)
    return jogos, tentativas


def _validar_dezenas(entrada: GeracaoEntrada) -> None:
    em_comum = sorted(set(entrada.obrigatorias) & set(entrada.excluidas))
    if em_comum:
        raise ErroDeNegocio(
            "uma dezena não pode ser obrigatória e excluída ao mesmo tempo: "
            + ", ".join(f"{d:02d}" for d in em_comum)
        )
    if len(entrada.obrigatorias) > entrada.dezenas_por_jogo:
        raise ErroDeNegocio(
            f"são {len(entrada.obrigatorias)} obrigatórias para jogos de "
            f"{entrada.dezenas_por_jogo} dezenas"
        )
    if 25 - len(entrada.excluidas) < entrada.dezenas_por_jogo:
        raise ErroDeNegocio(
            f"com {len(entrada.excluidas)} excluídas sobram menos de "
            f"{entrada.dezenas_por_jogo} dezenas"
        )


def _concurso_base(sessao: Session, numero: int | None) -> Concurso:
    if numero is None:
        concurso = sessao.scalar(select(Concurso).order_by(Concurso.numero.desc()).limit(1))
        if concurso is None:
            raise Conflito("Não há concursos no banco. Atualize os concursos primeiro.")
        return concurso
    concurso = sessao.scalar(select(Concurso).where(Concurso.numero == numero))
    if concurso is None:
        raise NaoEncontrado(f"Concurso {numero} não está no banco.")
    return concurso


def _jogo_saida(jogo: JogoGerado, base: list[int]) -> JogoSaida:
    return JogoSaida(
        id=jogo.id,
        sequencia=jogo.sequencia,
        dezenas=list(jogo.dezenas),
        perfil=PerfilSaida(**asdict(calcular_perfil(jogo.dezenas))),
        repetidas_do_concurso_base=repetidas(jogo.dezenas, base),
    )


def _resumo(geracao: GeracaoJogos) -> dict[str, Any]:
    p = geracao.parametros
    return {
        "id": geracao.id,
        "criada_em": geracao.criada_em,
        "estrategia_id": geracao.estrategia_id,
        "estrategia_nome": (p.get("estrategia") or {}).get("nome"),
        "concurso_base": geracao.concurso_base_numero,
        "quantidade_jogos": geracao.quantidade_jogos,
        "dezenas_por_jogo": geracao.dezenas_por_jogo,
        "obrigatorias": list(geracao.dezenas_obrigatorias),
        "excluidas": list(geracao.dezenas_excluidas),
        "regras": [FaixaSaida(**r) for r in p.get("regras", [])],
        "semente": geracao.semente,
    }


def gerar(sessao: Session, entrada: GeracaoEntrada) -> GeracaoSaida:
    _validar_dezenas(entrada)
    base = _concurso_base(sessao, entrada.concurso_base)

    estrategia = None
    regras: list[FaixaSaida] = []
    if entrada.estrategia_id is not None:
        estrategia = sessao.get(Estrategia, entrada.estrategia_id)
        if estrategia is None:
            raise NaoEncontrado(f"Estratégia {entrada.estrategia_id} não existe.")
        if not estrategia.ativa:
            raise ErroDeNegocio(f"A estratégia “{estrategia.nome}” está desativada.")
        regras = faixas_da_estrategia(sessao, estrategia.id)

    semente = (
        entrada.semente
        if entrada.semente is not None
        else random.SystemRandom().randrange(MAIOR_SEMENTE)
    )
    faixas = [Faixa(r.codigo, r.minimo, r.maximo) for r in regras]
    jogos, tentativas = sortear_jogos(
        entrada.quantidade,
        entrada.dezenas_por_jogo,
        entrada.obrigatorias,
        entrada.excluidas,
        faixas,
        list(base.dezenas),
        semente,
    )
    if len(jogos) < entrada.quantidade:
        raise ErroDeNegocio(
            f"Só foram encontrados {len(jogos)} de {entrada.quantidade} jogos que respeitam "
            f"todas as regras, em {tentativas:,} tentativas. Afrouxe alguma faixa ou reduza "
            "as dezenas obrigatórias e excluídas.".replace(",", ".")
        )

    geracao = GeracaoJogos(
        estrategia_id=estrategia.id if estrategia else None,
        concurso_base_numero=base.numero,
        quantidade_jogos=entrada.quantidade,
        dezenas_por_jogo=entrada.dezenas_por_jogo,
        dezenas_obrigatorias=entrada.obrigatorias,
        dezenas_excluidas=entrada.excluidas,
        parametros={
            "versao": 1,
            "estrategia": {"id": estrategia.id, "nome": estrategia.nome} if estrategia else None,
            "regras": [r.model_dump() for r in regras],
            "algoritmo": "sorteio com filtro (random.Random)",
        },
        semente=semente,
    )
    sessao.add(geracao)
    sessao.flush()
    registros = [
        JogoGerado(geracao_id=geracao.id, sequencia=i, dezenas=jogo)
        for i, jogo in enumerate(jogos, start=1)
    ]
    sessao.add_all(registros)
    sessao.commit()
    sessao.refresh(geracao)
    return GeracaoSaida(
        **_resumo(geracao),
        tentativas=tentativas,
        jogos=[_jogo_saida(j, list(base.dezenas)) for j in registros],
    )


def listar(
    sessao: Session, limite: int = 20, deslocamento: int = 0
) -> tuple[int, list[GeracaoResumo]]:
    total = sessao.scalar(select(func.count()).select_from(GeracaoJogos)) or 0
    geracoes = sessao.scalars(
        select(GeracaoJogos).order_by(GeracaoJogos.id.desc()).limit(limite).offset(deslocamento)
    ).all()
    return total, [GeracaoResumo(**_resumo(g)) for g in geracoes]


def buscar(sessao: Session, geracao_id: int) -> GeracaoJogos:
    geracao = sessao.get(GeracaoJogos, geracao_id)
    if geracao is None:
        raise NaoEncontrado(f"Geração {geracao_id} não existe.")
    return geracao


def obter(sessao: Session, geracao_id: int) -> GeracaoSaida:
    geracao = buscar(sessao, geracao_id)
    base = sessao.scalar(
        select(Concurso.dezenas).where(Concurso.numero == geracao.concurso_base_numero)
    )
    jogos = sessao.scalars(
        select(JogoGerado).where(JogoGerado.geracao_id == geracao_id).order_by(JogoGerado.sequencia)
    ).all()
    return GeracaoSaida(**_resumo(geracao), jogos=[_jogo_saida(j, list(base)) for j in jogos])
