"""Atualização dos concursos a partir da API da Caixa.

Busca apenas os concursos que faltam no banco (de 1 até o último sorteado), grava em lotes
e registra a execução em historico_importacoes.

Idempotência: o número do concurso é único e a gravação usa ON CONFLICT DO NOTHING, então
rodar de novo (ou duas atualizações ao mesmo tempo) nunca duplica concursos.

Transações: cada lote é gravado na sua própria transação. Se a Caixa parar de responder no
meio, os lotes já gravados ficam (são concursos completos e válidos), o histórico registra
FALHOU com o motivo, e a próxima execução continua de onde parou.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.integracoes.caixa import (
    ClienteCaixa,
    ConcursoNaoEncontrado,
    DadosInvalidosCaixa,
    ErroFonteExterna,
    ResultadoCaixa,
)
from app.models import Concurso, HistoricoImportacao

log = logging.getLogger("lotofacil.atualizacao")

TAMANHO_DO_LOTE = 50
MAXIMO_DE_REJEICOES_NA_MENSAGEM = 20

AoProgredir = Callable[[int, int], None]


@dataclass
class ResumoAtualizacao:
    importacao_id: int
    status: str
    ultimo_concurso_caixa: int
    ultimo_concurso_banco: int | None
    buscados: int
    inseridos: int
    ignorados: int
    rejeitados: int
    faltam: int
    mensagem: str


def numeros_faltando(sessao: Session, ate: int) -> list[int]:
    """Números de concurso entre 1 e `ate` que ainda não estão no banco (inclui lacunas)."""
    consulta = text(
        "SELECT n FROM generate_series(1, :ate) AS n "
        "EXCEPT SELECT numero FROM concursos ORDER BY 1"
    )
    return list(sessao.scalars(consulta, {"ate": ate}))


def _gravar(sessao: Session, resultado: ResultadoCaixa, importacao_id: int) -> bool:
    """Grava o concurso; devolve False se ele já existia."""
    comando = (
        insert(Concurso)
        .values(
            numero=resultado.numero,
            data_sorteio=resultado.data_sorteio,
            dezenas=resultado.dezenas,
            importacao_id=importacao_id,
        )
        .on_conflict_do_nothing(index_elements=[Concurso.numero])
        .returning(Concurso.numero)
    )
    return sessao.scalar(comando) is not None


def atualizar_concursos(
    sessao: Session,
    cliente: ClienteCaixa,
    limite: int | None = None,
    ao_progredir: AoProgredir | None = None,
) -> ResumoAtualizacao:
    """Busca na Caixa os concursos que faltam e grava no banco.

    `limite` restringe quantos concursos são buscados nesta execução (None = todos).
    `ao_progredir(feitos, total)` é chamado ao fim de cada lote.
    """
    ultimo = cliente.ultimo_concurso()
    ultimo_no_banco = sessao.scalar(select(func.max(Concurso.numero)))
    faltando = numeros_faltando(sessao, ultimo.numero)
    a_buscar = faltando if limite is None else faltando[:limite]

    historico = HistoricoImportacao(
        origem="API",
        referencia=f"{cliente.url_base} (concursos 1 a {ultimo.numero})",
        total_lidos=0,
        total_inseridos=0,
        total_ignorados=0,
        total_rejeitados=0,
    )
    sessao.add(historico)
    sessao.commit()

    rejeicoes: list[str] = []
    erro_fatal: str | None = None
    feitos = 0

    def registrar_lote() -> None:
        sessao.commit()
        if ao_progredir:
            ao_progredir(feitos, len(a_buscar))

    try:
        for numero in a_buscar:
            try:
                resultado = ultimo if numero == ultimo.numero else cliente.concurso(numero)
            except (ConcursoNaoEncontrado, DadosInvalidosCaixa) as erro:
                historico.total_rejeitados += 1
                rejeicoes.append(f"{numero}: {erro}")
            else:
                if _gravar(sessao, resultado, historico.id):
                    historico.total_inseridos += 1
                else:
                    historico.total_ignorados += 1
            historico.total_lidos += 1
            feitos += 1
            if feitos % TAMANHO_DO_LOTE == 0:
                registrar_lote()
    except ErroFonteExterna as erro:
        erro_fatal = str(erro)
        log.error("Atualização interrompida no concurso %s: %s", numero, erro)
    if feitos % TAMANHO_DO_LOTE or not a_buscar:
        registrar_lote()

    faltam = len(faltando) - historico.total_inseridos - historico.total_ignorados
    if erro_fatal:
        historico.status = "FALHOU"
    elif historico.total_rejeitados:
        historico.status = "CONCLUIDA_COM_REJEICOES"
    else:
        historico.status = "CONCLUIDA"

    partes = []
    if erro_fatal:
        partes.append(
            f"Interrompida: {erro_fatal}. Os concursos já gravados foram mantidos; "
            "rode a atualização de novo para continuar."
        )
    if rejeicoes:
        partes.append("Rejeitados: " + "; ".join(rejeicoes[:MAXIMO_DE_REJEICOES_NA_MENSAGEM]))
    historico.mensagem_erro = "\n".join(partes) or None
    historico.finalizada_em = datetime.now(UTC)
    sessao.commit()

    if not faltando:
        mensagem = f"Nada a fazer: o banco já tem todos os concursos até o {ultimo.numero}."
    elif erro_fatal:
        mensagem = partes[0]
    elif faltam > 0:
        mensagem = (
            f"{historico.total_inseridos} concursos gravados. Ainda faltam {faltam}; "
            "rode a atualização de novo para continuar."
        )
    else:
        mensagem = f"Banco atualizado até o concurso {ultimo.numero}."

    return ResumoAtualizacao(
        importacao_id=historico.id,
        status=historico.status,
        ultimo_concurso_caixa=ultimo.numero,
        ultimo_concurso_banco=sessao.scalar(select(func.max(Concurso.numero))),
        buscados=historico.total_lidos,
        inseridos=historico.total_inseridos,
        ignorados=historico.total_ignorados,
        rejeitados=historico.total_rejeitados,
        faltam=faltam,
        mensagem=mensagem,
    )
