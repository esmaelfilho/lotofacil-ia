"""Estratégias: conjuntos nomeados de regras com faixas (RF-04.2, RF-04.3)."""

from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.models import Estrategia, EstrategiaRegra, GeracaoJogos, RegraEstatistica
from app.schemas.jogos import EstrategiaEntrada, EstrategiaSaida, FaixaSaida, RegraSaida
from app.services.erros import Conflito, ErroDeNegocio, NaoEncontrado
from app.services.regras import Faixa, validar_faixa


def listar_regras(sessao: Session) -> list[RegraSaida]:
    regras = sessao.scalars(select(RegraEstatistica).order_by(RegraEstatistica.id)).all()
    return [RegraSaida.model_validate(r) for r in regras]


def _foi_usada(sessao: Session, estrategia_id: int) -> bool:
    return bool(sessao.scalar(select(exists().where(GeracaoJogos.estrategia_id == estrategia_id))))


def faixas_da_estrategia(sessao: Session, estrategia_id: int) -> list[FaixaSaida]:
    linhas = sessao.execute(
        select(RegraEstatistica.codigo, RegraEstatistica.nome, EstrategiaRegra.parametros)
        .join(EstrategiaRegra, EstrategiaRegra.regra_id == RegraEstatistica.id)
        .where(EstrategiaRegra.estrategia_id == estrategia_id)
        .order_by(RegraEstatistica.id)
    ).all()
    return [
        FaixaSaida(
            codigo=linha.codigo,
            nome=linha.nome,
            minimo=linha.parametros["minimo"],
            maximo=linha.parametros["maximo"],
        )
        for linha in linhas
    ]


def _saida(sessao: Session, estrategia: Estrategia) -> EstrategiaSaida:
    return EstrategiaSaida(
        id=estrategia.id,
        nome=estrategia.nome,
        descricao=estrategia.descricao,
        ativa=estrategia.ativa,
        criada_em=estrategia.criada_em,
        atualizada_em=estrategia.atualizada_em,
        usada=_foi_usada(sessao, estrategia.id),
        regras=faixas_da_estrategia(sessao, estrategia.id),
    )


def _buscar(sessao: Session, estrategia_id: int) -> Estrategia:
    estrategia = sessao.get(Estrategia, estrategia_id)
    if estrategia is None:
        raise NaoEncontrado(f"Estratégia {estrategia_id} não existe.")
    return estrategia


def _validar(sessao: Session, entrada: EstrategiaEntrada, ignorar_id: int | None = None):
    codigos = [r.codigo for r in entrada.regras]
    repetidos = sorted({c for c in codigos if codigos.count(c) > 1})
    if repetidos:
        raise ErroDeNegocio(f"regra repetida na estratégia: {', '.join(repetidos)}")
    faixas = [validar_faixa(r.codigo, r.minimo, r.maximo) for r in entrada.regras]
    regras = {
        r.codigo: r
        for r in sessao.scalars(
            select(RegraEstatistica).where(RegraEstatistica.codigo.in_(codigos))
        )
    }
    for f in faixas:
        if f.codigo not in regras:
            raise ErroDeNegocio(f"regra desconhecida: {f.codigo}")
        if not regras[f.codigo].ativa:
            raise ErroDeNegocio(f"a regra {f.codigo} está desativada")
    mesmo_nome = select(Estrategia.id).where(func.lower(Estrategia.nome) == entrada.nome.lower())
    if ignorar_id is not None:
        mesmo_nome = mesmo_nome.where(Estrategia.id != ignorar_id)
    if sessao.scalar(mesmo_nome) is not None:
        raise Conflito(f"Já existe uma estratégia chamada “{entrada.nome}”.")
    return faixas, regras


def _gravar_regras(
    sessao: Session,
    estrategia: Estrategia,
    faixas: list[Faixa],
    regras: dict[str, RegraEstatistica],
) -> None:
    for f in faixas:
        sessao.add(
            EstrategiaRegra(
                estrategia_id=estrategia.id,
                regra_id=regras[f.codigo].id,
                parametros={"minimo": f.minimo, "maximo": f.maximo},
            )
        )


def listar(sessao: Session, incluir_inativas: bool = True) -> list[EstrategiaSaida]:
    consulta = select(Estrategia).order_by(Estrategia.nome)
    if not incluir_inativas:
        consulta = consulta.where(Estrategia.ativa)
    return [_saida(sessao, e) for e in sessao.scalars(consulta).all()]


def obter(sessao: Session, estrategia_id: int) -> EstrategiaSaida:
    return _saida(sessao, _buscar(sessao, estrategia_id))


def criar(sessao: Session, entrada: EstrategiaEntrada) -> EstrategiaSaida:
    faixas, regras = _validar(sessao, entrada)
    estrategia = Estrategia(nome=entrada.nome, descricao=entrada.descricao)
    sessao.add(estrategia)
    sessao.flush()
    _gravar_regras(sessao, estrategia, faixas, regras)
    sessao.commit()
    sessao.refresh(estrategia)
    return _saida(sessao, estrategia)


def atualizar(sessao: Session, estrategia_id: int, entrada: EstrategiaEntrada) -> EstrategiaSaida:
    """Troca nome, descrição e regras. Gerações antigas não mudam: elas guardam uma cópia."""
    estrategia = _buscar(sessao, estrategia_id)
    faixas, regras = _validar(sessao, entrada, ignorar_id=estrategia_id)
    estrategia.nome = entrada.nome
    estrategia.descricao = entrada.descricao
    estrategia.atualizada_em = func.now()
    sessao.execute(delete(EstrategiaRegra).where(EstrategiaRegra.estrategia_id == estrategia_id))
    _gravar_regras(sessao, estrategia, faixas, regras)
    sessao.commit()
    sessao.refresh(estrategia)
    return _saida(sessao, estrategia)


def alterar_ativa(sessao: Session, estrategia_id: int, ativa: bool) -> EstrategiaSaida:
    estrategia = _buscar(sessao, estrategia_id)
    estrategia.ativa = ativa
    sessao.commit()
    sessao.refresh(estrategia)
    return _saida(sessao, estrategia)


def excluir(sessao: Session, estrategia_id: int) -> None:
    estrategia = _buscar(sessao, estrategia_id)
    if _foi_usada(sessao, estrategia_id):
        raise Conflito(
            "Esta estratégia já foi usada em gerações de jogos e não pode ser excluída. "
            "Desative-a."
        )
    sessao.delete(estrategia)
    sessao.commit()
