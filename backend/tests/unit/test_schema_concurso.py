"""T05 (parte do backend): validação das dezenas com Pydantic."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.concurso import ConcursoEntrada

QUINZE = [25, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 2, 4]


def test_dezenas_validas_sao_ordenadas():
    concurso = ConcursoEntrada(numero=1, data_sorteio=date(2003, 9, 29), dezenas=QUINZE)
    assert concurso.dezenas == sorted(QUINZE)


@pytest.mark.parametrize(
    ("dezenas", "trecho"),
    [
        (list(range(1, 15)), "15 dezenas; foram informadas 14"),
        (list(range(1, 17)), "15 dezenas; foram informadas 16"),
        ([1, 1] + list(range(3, 16)), "repetidas: 01"),
        ([0] + list(range(2, 16)), "fora do intervalo de 01 a 25: 0"),
        (list(range(2, 16)) + [26], "fora do intervalo de 01 a 25: 26"),
    ],
)
def test_dezenas_invalidas(dezenas, trecho):
    with pytest.raises(ValidationError) as erro:
        ConcursoEntrada(numero=1, data_sorteio=date(2003, 9, 29), dezenas=dezenas)
    assert trecho in str(erro.value)


def test_numero_do_concurso_deve_ser_positivo():
    with pytest.raises(ValidationError):
        ConcursoEntrada(numero=0, data_sorteio=date(2003, 9, 29), dezenas=QUINZE)
