"""T06 (sem banco): perfil de uma lista de dezenas, conferido à mão."""

from app.services.estatisticas.perfil import calcular_perfil, repetidas, sequencias
from tests.estatisticas_conhecidas import C1, C2, C3, C5


def test_perfil_de_um_concurso_variado():
    p = calcular_perfil(C5)  # 1 2 3 5 6 8 10 12 14 16 18 20 22 23 24
    assert (p.pares, p.impares) == (11, 4)
    assert p.primos == 4  # 2 3 5 23
    assert p.soma == 184
    assert (p.miolo, p.moldura) == (4, 11)  # miolo: 8 12 14 18
    assert p.por_linha == (4, 3, 2, 3, 3)
    assert p.por_coluna == (3, 3, 4, 2, 3)
    assert p.maior_sequencia == 3  # 1-2-3 e 22-23-24
    assert p.blocos_consecutivos == 3  # 1-2-3, 5-6, 22-23-24
    assert p.fibonacci == 5  # 1 2 3 5 8
    assert p.multiplos_de_3 == 5  # 3 6 12 18 24


def test_perfil_de_1_a_15():
    p = calcular_perfil(C1)
    assert (p.pares, p.impares, p.primos, p.soma) == (7, 8, 6, 120)
    assert (p.miolo, p.moldura) == (6, 9)
    assert p.por_linha == (5, 5, 5, 0, 0)
    assert p.por_coluna == (3, 3, 3, 3, 3)
    assert (p.maior_sequencia, p.blocos_consecutivos) == (15, 1)
    assert (p.fibonacci, p.multiplos_de_3) == (6, 5)


def test_somas_dos_totais_fecham_em_15():
    for dezenas in (C1, C2, C5):
        p = calcular_perfil(dezenas)
        assert p.pares + p.impares == p.miolo + p.moldura == 15
        assert sum(p.por_linha) == sum(p.por_coluna) == 15


def test_sequencias_e_ordem_nao_importa():
    assert sequencias([8, 6, 5, 3, 2, 1]) == [3, 2, 1]
    assert sequencias([]) == []
    assert calcular_perfil(list(reversed(C5))) == calcular_perfil(C5)


def test_sem_sequencia():
    p = calcular_perfil([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25])
    assert (p.maior_sequencia, p.blocos_consecutivos) == (1, 0)


def test_repetidas():
    assert repetidas(C2, C1) == 6  # 10 a 15
    assert repetidas(C5, C3) == 9  # 1 2 3 5 6 8 10 12 14
    assert repetidas(C1, C3) == 15
