"""T03, T04 e T05 (banco): inserção, consulta, duplicidade e restrições das dezenas."""

from datetime import date

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import Concurso

DEZENAS = [1, 2, 3, 5, 8, 10, 11, 13, 14, 17, 19, 20, 21, 23, 25]


def test_insere_e_consulta_concurso(sessao):
    sessao.add(Concurso(numero=1, data_sorteio=date(2003, 9, 29), dezenas=DEZENAS))
    sessao.commit()
    lido = sessao.scalars(select(Concurso).where(Concurso.numero == 1)).one()
    assert lido.dezenas == DEZENAS
    assert lido.data_sorteio == date(2003, 9, 29)
    assert lido.criado_em is not None


def test_numero_duplicado_e_recusado(sessao):
    sessao.add(Concurso(numero=10, data_sorteio=date(2003, 10, 1), dezenas=DEZENAS))
    sessao.commit()
    sessao.add(Concurso(numero=10, data_sorteio=date(2003, 10, 2), dezenas=DEZENAS))
    with pytest.raises(IntegrityError, match="uq_concursos_numero"):
        sessao.commit()


@pytest.mark.parametrize(
    "dezenas",
    [
        "{1,2,3,4,5,6,7,8,9,10,11,12,13,14}",  # 14 dezenas
        "{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}",  # 16 dezenas
        "{1,1,3,4,5,6,7,8,9,10,11,12,13,14,15}",  # repetida
        "{0,2,3,4,5,6,7,8,9,10,11,12,13,14,15}",  # zero
        "{2,3,4,5,6,7,8,9,10,11,12,13,14,15,26}",  # 26
        "{2,1,3,4,5,6,7,8,9,10,11,12,13,14,15}",  # fora de ordem
        "{NULL,2,3,4,5,6,7,8,9,10,11,12,13,14,15}",  # nulo
        "{{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}}",  # duas dimensões
        "{}",  # vazio
    ],
)
def test_banco_recusa_dezenas_invalidas_mesmo_sem_o_backend(conexao, dezenas):
    with pytest.raises(IntegrityError, match="ck_concursos_dezenas"):
        conexao.execute(
            text(
                "INSERT INTO concursos (numero, data_sorteio, dezenas) "
                "VALUES (99, DATE '2003-09-29', CAST(:d AS smallint[]))"
            ),
            {"d": dezenas},
        )


def test_numero_zero_e_recusado(conexao):
    with pytest.raises(IntegrityError, match="ck_concursos_numero_positivo"):
        conexao.execute(
            text(
                "INSERT INTO concursos (numero, data_sorteio, dezenas) "
                "VALUES (0, DATE '2003-09-29', '{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}')"
            )
        )


def test_reimportacao_com_on_conflict_nao_duplica(conexao):
    inserir = text(
        "INSERT INTO concursos (numero, data_sorteio, dezenas) "
        "VALUES (:n, DATE '2003-09-29', '{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}') "
        "ON CONFLICT (numero) DO NOTHING RETURNING numero"
    )
    assert conexao.execute(inserir, {"n": 50}).scalar() == 50
    assert conexao.execute(inserir, {"n": 50}).scalar() is None
    assert conexao.scalar(text("SELECT count(*) FROM concursos WHERE numero = 50")) == 1
