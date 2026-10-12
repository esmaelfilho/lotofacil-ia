"""T07 e T08: atualização idempotente pela API da Caixa (simulada) e tratamento de erros."""

from sqlalchemy import func, select

from app.models import Concurso, HistoricoImportacao
from app.services import atualizacao
from app.services.atualizacao import atualizar_concursos
from tests.fakes import CaixaFalsa


def _numeros(sessao):
    return list(sessao.scalars(select(Concurso.numero).order_by(Concurso.numero)))


def test_primeira_carga_grava_todos_os_concursos(sessao):
    caixa = CaixaFalsa(ultimo=30)
    resumo = atualizar_concursos(sessao, caixa.cliente())
    assert resumo.inseridos == 30
    assert resumo.faltam == 0
    assert resumo.status == "CONCLUIDA"
    assert _numeros(sessao) == list(range(1, 31))
    historico = sessao.get(HistoricoImportacao, resumo.importacao_id)
    assert (historico.origem, historico.total_inseridos) == ("API", 30)
    assert historico.finalizada_em is not None
    concurso = sessao.scalar(select(Concurso).where(Concurso.numero == 7))
    assert concurso.importacao_id == resumo.importacao_id
    assert concurso.dezenas == sorted(concurso.dezenas)


def test_segunda_execucao_nao_duplica_nem_busca_de_novo(sessao):
    atualizar_concursos(sessao, CaixaFalsa(ultimo=20).cliente())
    caixa = CaixaFalsa(ultimo=20)
    resumo = atualizar_concursos(sessao, caixa.cliente())
    assert resumo.inseridos == 0
    assert "Nada a fazer" in resumo.mensagem
    assert len(caixa.pedidos) == 1  # só a consulta do último concurso
    assert sessao.scalar(select(func.count()).select_from(Concurso)) == 20


def test_busca_somente_os_novos_e_preenche_lacunas(sessao):
    atualizar_concursos(sessao, CaixaFalsa(ultimo=10).cliente())
    sessao.execute(Concurso.__table__.delete().where(Concurso.numero.in_([3, 4])))
    sessao.commit()
    caixa = CaixaFalsa(ultimo=13)
    resumo = atualizar_concursos(sessao, caixa.cliente())
    assert resumo.inseridos == 5  # 3, 4, 11, 12, 13
    assert _numeros(sessao) == list(range(1, 14))


def test_limite_por_execucao_e_continuacao(sessao):
    caixa = CaixaFalsa(ultimo=25)
    primeira = atualizar_concursos(sessao, caixa.cliente(), limite=10)
    assert (primeira.inseridos, primeira.faltam) == (10, 15)
    assert "Ainda faltam 15" in primeira.mensagem
    segunda = atualizar_concursos(sessao, caixa.cliente())
    assert (segunda.inseridos, segunda.faltam) == (15, 0)


def test_falha_no_meio_mantem_lotes_gravados_e_registra(sessao, monkeypatch):
    monkeypatch.setattr(atualizacao, "TAMANHO_DO_LOTE", 5)
    caixa = CaixaFalsa(ultimo=20, falhar_em=13)
    resumo = atualizar_concursos(sessao, caixa.cliente())
    assert resumo.status == "FALHOU"
    assert resumo.inseridos == 12
    assert _numeros(sessao) == list(range(1, 13))
    historico = sessao.get(HistoricoImportacao, resumo.importacao_id)
    assert historico.status == "FALHOU"
    assert "tempo esgotado" in historico.mensagem_erro
    # a próxima execução continua de onde parou
    retomada = atualizar_concursos(sessao, CaixaFalsa(ultimo=20).cliente())
    assert (retomada.inseridos, retomada.faltam) == (8, 0)


def test_concursos_invalidos_ou_inexistentes_sao_rejeitados(sessao):
    caixa = CaixaFalsa(ultimo=10, invalidos={4}, inexistentes={6})
    resumo = atualizar_concursos(sessao, caixa.cliente())
    assert resumo.status == "CONCLUIDA_COM_REJEICOES"
    assert (resumo.inseridos, resumo.rejeitados, resumo.faltam) == (8, 2, 2)
    historico = sessao.get(HistoricoImportacao, resumo.importacao_id)
    assert "4: concurso 4 com dezenas inválidas" in historico.mensagem_erro
    assert "6:" in historico.mensagem_erro
    assert 4 not in _numeros(sessao)
