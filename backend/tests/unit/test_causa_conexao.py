"""T01: a causa provável é reconhecida em inglês, em português e com acentos corrompidos."""

import pytest

from app.db.verificacao import _causa_provavel

SENHA = "usuário ou senha recusados"
INEXISTENTE = "não existe"
SEM_SERVIDOR = "não há servidor PostgreSQL"


@pytest.mark.parametrize(
    ("detalhe", "esperado"),
    [
        ('FATAL:  password authentication failed for user "lotofacil_app"', SENHA),
        ('FATAL:  autenticação do tipo senha falhou para o usuário "lotofacil_app"', SENHA),
        ('FATAL:  autentica��o do tipo senha falhou para o usu�rio "x"', SENHA),
        ('FATAL:  database "nao_existe_test" does not exist', INEXISTENTE),
        ('FATAL:  banco de dados "nao_existe_test" não existe', INEXISTENTE),
        ('FATAL:  banco de dados "nao_existe_test" n�o existe', INEXISTENTE),
        ("connection failed: Connection refused", SEM_SERVIDOR),
        ("connection failed: timeout expired", "não respondeu a tempo"),
    ],
)
def test_causa_provavel(detalhe, esperado):
    assert esperado in _causa_provavel(detalhe)


def test_causa_desconhecida():
    assert "erro inesperado" in _causa_provavel("algo totalmente diferente")
