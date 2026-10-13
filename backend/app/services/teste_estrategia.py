"""Testar estratégias em um concurso que já saiu (RF-07).

Os jogos são gerados como se fosse a véspera do concurso testado: a base é o concurso
anterior a ele, e o resultado testado não é usado para gerar. Depois, os jogos são
conferidos contra o resultado. Nada é gravado.

Cada estratégia usa a mesma semente e o mesmo sorteio de `geracao.sortear_jogos`. Por isso,
`POST /geracoes` com os mesmos parâmetros, a mesma semente e `concurso_base` igual ao
concurso anterior grava exatamente os jogos mostrados no teste.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Concurso
from app.schemas.jogos import (
    EntradaTesteEstrategia,
    JogoTestado,
    ResultadoDoTeste,
    SaidaTesteEstrategia,
)
from app.services.avaliacao import PONTOS_PREMIADOS
from app.services.erros import ErroDeNegocio, NaoEncontrado
from app.services.geracao import (
    estrategia_e_regras,
    semente_ou_sorteada,
    sortear_jogos,
    validar_dezenas,
)
from app.services.regras import Faixa


def _concursos(sessao: Session, numero: int) -> tuple[Concurso, Concurso]:
    """O concurso testado e o anterior a ele (a base)."""
    testado = sessao.scalar(select(Concurso).where(Concurso.numero == numero))
    if testado is None:
        raise NaoEncontrado(f"Concurso {numero} não está no banco.")
    anterior = sessao.scalar(
        select(Concurso).where(Concurso.numero < numero).order_by(Concurso.numero.desc()).limit(1)
    )
    if anterior is None:
        raise ErroDeNegocio(
            f"Não há concurso anterior ao {numero} no banco para servir de base. "
            "Escolha um concurso mais recente."
        )
    return testado, anterior


def testar(sessao: Session, entrada: EntradaTesteEstrategia) -> SaidaTesteEstrategia:
    if not entrada.estrategia_ids and not entrada.incluir_aleatorio:
        raise ErroDeNegocio("Escolha pelo menos uma estratégia ou os jogos aleatórios.")
    validar_dezenas(entrada.dezenas_por_jogo, entrada.obrigatorias, entrada.excluidas)
    testado, base = _concursos(sessao, entrada.concurso)
    semente = semente_ou_sorteada(entrada.semente)
    sorteadas = set(testado.dezenas)

    opcoes: list[int | None] = list(entrada.estrategia_ids)
    if entrada.incluir_aleatorio:
        opcoes.append(None)

    resultados = []
    for estrategia_id in opcoes:
        estrategia, regras = estrategia_e_regras(sessao, estrategia_id)
        jogos, tentativas = sortear_jogos(
            entrada.quantidade,
            entrada.dezenas_por_jogo,
            entrada.obrigatorias,
            entrada.excluidas,
            [Faixa(r.codigo, r.minimo, r.maximo) for r in regras],
            list(base.dezenas),
            semente,
        )
        testados = []
        for i, jogo in enumerate(jogos, start=1):
            acertadas = sorted(sorteadas & set(jogo))
            testados.append(
                JogoTestado(
                    sequencia=i, dezenas=jogo, acertos=len(acertadas), dezenas_acertadas=acertadas
                )
            )
        acertos = [j.acertos for j in testados]
        aviso = None
        if len(jogos) < entrada.quantidade:
            aviso = (
                f"Só foram encontrados {len(jogos)} de {entrada.quantidade} jogos que respeitam "
                f"todas as regras, em {tentativas:,} tentativas.".replace(",", ".")
            )
        resultados.append(
            ResultadoDoTeste(
                estrategia_id=estrategia.id if estrategia else None,
                estrategia_nome=estrategia.nome if estrategia else None,
                regras=regras,
                jogos=testados,
                maior_acerto=max(acertos, default=None),
                media_acertos=round(sum(acertos) / len(acertos), 2) if acertos else None,
                por_acertos={p: acertos.count(p) for p in PONTOS_PREMIADOS},
                aviso=aviso,
            )
        )

    return SaidaTesteEstrategia(
        concurso=testado.numero,
        dezenas_sorteadas=list(testado.dezenas),
        concurso_base=base.numero,
        quantidade=entrada.quantidade,
        dezenas_por_jogo=entrada.dezenas_por_jogo,
        obrigatorias=entrada.obrigatorias,
        excluidas=entrada.excluidas,
        semente=semente,
        resultados=resultados,
    )
