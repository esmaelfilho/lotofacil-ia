"""Conferência de jogos (RF-06).

- Uma geração contra um concurso: calcula os acertos e grava em `avaliacoes` (RF-06.1).
  Conferir de novo o mesmo concurso não duplica (ON CONFLICT).
- Um jogo contra todo o histórico: só consulta (RF-06.2).
"""

from collections import Counter

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Avaliacao, Concurso, JogoGerado
from app.schemas.jogos import ConferenciaHistoricoSaida, ConferenciaSaida, JogoConferido
from app.services.erros import NaoEncontrado
from app.services.geracao import buscar

PONTOS_PREMIADOS = (11, 12, 13, 14, 15)


def conferir_geracao(sessao: Session, geracao_id: int, numero_concurso: int) -> ConferenciaSaida:
    buscar(sessao, geracao_id)
    concurso = sessao.scalar(select(Concurso).where(Concurso.numero == numero_concurso))
    if concurso is None:
        raise NaoEncontrado(f"Concurso {numero_concurso} não está no banco.")
    sorteadas = set(concurso.dezenas)
    jogos = sessao.scalars(
        select(JogoGerado).where(JogoGerado.geracao_id == geracao_id).order_by(JogoGerado.sequencia)
    ).all()

    conferidos = []
    for jogo in jogos:
        acertadas = sorted(sorteadas & set(jogo.dezenas))
        conferidos.append(
            JogoConferido(
                jogo_id=jogo.id,
                sequencia=jogo.sequencia,
                dezenas=list(jogo.dezenas),
                acertos=len(acertadas),
                dezenas_acertadas=acertadas,
            )
        )
    if conferidos:
        sessao.execute(
            insert(Avaliacao)
            .values(
                [
                    {"jogo_id": c.jogo_id, "concurso_id": concurso.id, "acertos": c.acertos}
                    for c in conferidos
                ]
            )
            .on_conflict_do_nothing(index_elements=["jogo_id", "concurso_id"])
        )
    sessao.commit()
    contagem = Counter(c.acertos for c in conferidos)
    return ConferenciaSaida(
        geracao_id=geracao_id,
        concurso=concurso.numero,
        dezenas_sorteadas=list(concurso.dezenas),
        jogos=conferidos,
        por_acertos=dict(sorted(contagem.items(), reverse=True)),
    )


_HISTORICO = text("""
    SELECT acertos, count(*) AS vezes, max(numero) AS ultimo
    FROM (
      SELECT numero,
             cardinality(ARRAY(
               SELECT unnest(dezenas) INTERSECT SELECT unnest(CAST(:jogo AS smallint[]))
             )) AS acertos
      FROM concursos
    ) t
    GROUP BY acertos
""")


def conferir_historico(sessao: Session, dezenas: list[int]) -> ConferenciaHistoricoSaida:
    linhas = sessao.execute(_HISTORICO, {"jogo": dezenas}).all()
    total = sum(linha.vezes for linha in linhas)
    por_acertos = {p: 0 for p in PONTOS_PREMIADOS}
    ultimo = None
    for linha in linhas:
        if linha.acertos in por_acertos:
            por_acertos[linha.acertos] = linha.vezes
            ultimo = max(ultimo or 0, linha.ultimo)
    return ConferenciaHistoricoSaida(
        dezenas=dezenas,
        concursos=total,
        por_acertos=por_acertos,
        maior_acerto=max((linha.acertos for linha in linhas), default=None),
        ultimo_concurso_com_11_ou_mais=ultimo,
    )
