"""T06: estatísticas calculadas no PostgreSQL.

Dois tipos de conferência:
- um conjunto pequeno com valores conferidos à mão (tests/estatisticas_conhecidas.py);
- 300 concursos aleatórios (semente fixa), comparando o resultado do banco com um cálculo
  direto em Python, mais simples e independente das consultas SQL.
"""

import random
from collections import Counter
from datetime import date, timedelta
from itertools import combinations

import pytest

from app.models import Concurso
from app.services.estatisticas.atraso import atrasos
from app.services.estatisticas.combinacoes import combinacoes
from app.services.estatisticas.distribuicao import Caracteristica, distribuicao, perfis
from app.services.estatisticas.filtros import filtrar_dezenas
from app.services.estatisticas.frequencia import frequencia, quentes_e_frias
from app.services.estatisticas.perfil import calcular_perfil
from tests.estatisticas_conhecidas import CONCURSOS, FREQUENCIA_TOTAL


def _gravar(sessao, concursos):
    sessao.add_all(Concurso(numero=n, data_sorteio=d, dezenas=z) for n, d, z in concursos)
    sessao.commit()


@pytest.fixture
def conhecidos(sessao):
    _gravar(sessao, CONCURSOS)
    return sessao


@pytest.fixture
def aleatorios(sessao):
    gerador = random.Random(2026)
    concursos = [
        (n, date(2020, 1, 1) + timedelta(days=n), sorted(gerador.sample(range(1, 26), 15)))
        for n in range(1, 301)
        if n not in (40, 41, 200)  # lacunas na numeração
    ]
    _gravar(sessao, concursos)
    return sessao, [z for _, _, z in concursos]  # em ordem crescente de número


# ---------- valores conferidos à mão ----------


def test_frequencia_conhecida(conhecidos):
    r = frequencia(conhecidos, (2, 10))
    assert r.concursos == 4
    assert {f.dezena: f.total for f in r.dezenas} == FREQUENCIA_TOTAL
    por_dezena = {f.dezena: f for f in r.dezenas}
    assert por_dezena[10].janelas == {2: 2, 10: 4}
    assert por_dezena[4].janelas[2] == 1  # só no concurso 3
    assert por_dezena[17].janelas[2] == 0
    assert por_dezena[25].total == 0 and por_dezena[25].percentual == 0
    assert por_dezena[10].percentual == 100.0
    assert por_dezena[17].percentual == 25.0


def test_quentes_e_frias_conhecidas(conhecidos):
    r = quentes_e_frias(conhecidos, janela=4, quantidade=3)
    assert [q.dezena for q in r.quentes] == [10, 12, 14]
    assert [f.dezena for f in r.frias] == [25, 17, 19]
    assert r.concursos_na_janela == 4
    assert quentes_e_frias(conhecidos, janela=50).concursos_na_janela == 4


def test_atrasos_conhecidos_com_lacuna_e_dezena_que_nunca_saiu(conhecidos):
    r = {a.dezena: a for a in atrasos(conhecidos).dezenas}
    assert (r[1].atraso_atual, r[1].maior_atraso, r[1].ultimo_concurso) == (0, 1, 5)
    assert (r[4].atraso_atual, r[4].maior_atraso, r[4].ultimo_concurso) == (1, 1, 3)
    assert (r[17].atraso_atual, r[17].maior_atraso, r[17].ultimo_concurso) == (2, 2, 2)
    assert (r[11].atraso_atual, r[11].maior_atraso) == (1, 1)
    assert (r[25].atraso_atual, r[25].maior_atraso, r[25].ultimo_concurso) == (4, 4, None)


def test_perfis_conhecidos(conhecidos):
    pagina = perfis(conhecidos, limite=2)
    assert pagina.total == 4
    assert [p.numero for p in pagina.itens] == [5, 3]
    c5 = pagina.itens[0]
    assert c5.perfil.soma == 184 and c5.perfil.por_linha == [4, 3, 2, 3, 3]
    assert c5.repetidas_do_anterior == 9  # comparado ao 3 (não existe o 4)
    assert pagina.itens[1].repetidas_do_anterior == 6  # 3 comparado ao 2

    ultima = perfis(conhecidos, limite=10, deslocamento=3)
    assert [p.numero for p in ultima.itens] == [1]
    assert ultima.itens[0].repetidas_do_anterior is None  # primeiro concurso do banco


def test_distribuicao_conhecida(conhecidos):
    r = distribuicao(conhecidos, Caracteristica.pares)
    assert r.concursos == 4
    assert [(v.valor, v.concursos) for v in r.valores] == [(7, 2), (8, 1), (11, 1)]
    assert (r.minimo, r.maximo, r.media) == (7, 11, 8.25)
    assert r.valores[0].percentual == 50.0

    rep = distribuicao(conhecidos, Caracteristica.repetidas_do_anterior)
    assert rep.concursos == 3  # o primeiro concurso não tem anterior
    assert [(v.valor, v.concursos) for v in rep.valores] == [(6, 2), (9, 1)]

    linha_4 = distribuicao(conhecidos, Caracteristica.linha_4)
    assert [(v.valor, v.concursos) for v in linha_4.valores] == [(0, 2), (3, 1), (5, 1)]

    ultimos_2 = distribuicao(conhecidos, Caracteristica.repetidas_do_anterior, ultimos=2)
    assert [(v.valor, v.concursos) for v in ultimos_2.valores] == [(6, 1), (9, 1)]


def test_obrigatorias_e_excluidas_conhecidas(conhecidos):
    r = filtrar_dezenas(conhecidos, [12, 10], [25])
    assert (r.concursos_atendidos, r.concursos_analisados, r.percentual) == (4, 4, 100.0)
    assert r.obrigatorias == [10, 12]

    r = filtrar_dezenas(conhecidos, [1], [16])
    assert (r.concursos_atendidos, r.ultimo_concurso_atendido) == (2, 3)

    r = filtrar_dezenas(conhecidos, [17], [])
    assert (r.concursos_atendidos, r.ultimo_concurso_atendido) == (1, 2)

    r = filtrar_dezenas(conhecidos, [1], [16], ultimos=2)
    assert (r.concursos_analisados, r.concursos_atendidos) == (2, 1)

    r = filtrar_dezenas(conhecidos, [25], [])
    assert (r.concursos_atendidos, r.ultimo_concurso_atendido, r.percentual) == (0, None, 0)


@pytest.mark.parametrize(
    ("obrigatorias", "excluidas", "mensagem"),
    [
        ([], [], "ao menos uma"),
        ([1, 26], [], "obrigatórias: dezenas fora"),
        ([3, 3], [], "repetidas"),
        ([5], [5, 6], "ao mesmo tempo: 05"),
        ([], list(range(1, 12)), "excluídas: são necessárias de 0 a 10"),
    ],
)
def test_filtro_invalido(conhecidos, obrigatorias, excluidas, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        filtrar_dezenas(conhecidos, obrigatorias, excluidas)


def test_combinacoes_conhecidas(conhecidos):
    pares = combinacoes(conhecidos, tamanho=2, quantidade=3)
    assert [(c.dezenas, c.vezes) for c in pares.combinacoes] == [
        ([10, 12], 4),
        ([10, 14], 4),
        ([12, 14], 4),
    ]
    trios = combinacoes(conhecidos, tamanho=3, quantidade=1)
    assert [(c.dezenas, c.vezes, c.percentual) for c in trios.combinacoes] == [
        ([10, 12, 14], 4, 100.0)
    ]
    ultimo = combinacoes(conhecidos, tamanho=2, quantidade=1, ultimos=1)
    assert ultimo.concursos == 1 and ultimo.combinacoes[0].vezes == 1


def test_banco_vazio_nao_quebra(sessao):
    assert frequencia(sessao).concursos == 0
    assert all(a.atraso_atual == 0 for a in atrasos(sessao).dezenas)
    assert quentes_e_frias(sessao).concursos_na_janela == 0
    assert perfis(sessao).itens == []
    assert distribuicao(sessao, Caracteristica.soma).media is None
    assert combinacoes(sessao).combinacoes == []
    assert filtrar_dezenas(sessao, [1], []).concursos_atendidos == 0


# ---------- 300 concursos aleatórios x cálculo direto em Python ----------


def test_frequencia_confere_com_python(aleatorios):
    sessao, todos = aleatorios
    r = frequencia(sessao, (10, 50, 100))
    for f in r.dezenas:
        assert f.total == sum(f.dezena in z for z in todos)
        for j in (10, 50, 100):
            assert f.janelas[j] == sum(f.dezena in z for z in todos[-j:])


def test_atrasos_conferem_com_python(aleatorios):
    sessao, todos = aleatorios
    r = {a.dezena: a for a in atrasos(sessao).dezenas}
    for d in range(1, 26):
        atual = maior = 0
        for z in todos:
            atual = 0 if d in z else atual + 1
            maior = max(maior, atual)
        assert (r[d].atraso_atual, r[d].maior_atraso) == (atual, maior), d


def test_combinacoes_conferem_com_python(aleatorios):
    sessao, todos = aleatorios
    for tamanho in (2, 3):
        contagem = Counter(c for z in todos for c in combinations(z, tamanho))
        esperado = sorted(contagem.items(), key=lambda item: (-item[1], item[0]))[:10]
        r = combinacoes(sessao, tamanho=tamanho, quantidade=10)
        assert [(tuple(c.dezenas), c.vezes) for c in r.combinacoes] == esperado

    contagem = Counter(c for z in todos[-30:] for c in combinations(z, 2))
    r = combinacoes(sessao, tamanho=2, quantidade=1, ultimos=30)
    assert r.combinacoes[0].vezes == max(contagem.values())


def test_distribuicao_e_filtro_conferem_com_python(aleatorios):
    sessao, todos = aleatorios
    esperado = Counter(calcular_perfil(z).soma for z in todos[-100:])
    r = distribuicao(sessao, Caracteristica.soma, ultimos=100)
    assert {v.valor: v.concursos for v in r.valores} == esperado

    esperado_rep = Counter(len(set(a) & set(b)) for a, b in zip(todos[1:], todos, strict=False))
    r = distribuicao(sessao, Caracteristica.repetidas_do_anterior)
    assert {v.valor: v.concursos for v in r.valores} == esperado_rep

    r = filtrar_dezenas(sessao, [1, 2], [3])
    assert r.concursos_atendidos == sum(1 in z and 2 in z and 3 not in z for z in todos)
