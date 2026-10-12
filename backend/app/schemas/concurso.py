"""Modelos Pydantic de concursos, com a validação das dezenas da Lotofácil."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEZENA_MINIMA = 1
DEZENA_MAXIMA = 25
DEZENAS_POR_RESULTADO = 15


def normalizar_dezenas(dezenas: list[int], minimo: int, maximo: int) -> list[int]:
    """Valida e devolve as dezenas em ordem crescente (ADR-002)."""
    fora = sorted({d for d in dezenas if not DEZENA_MINIMA <= d <= DEZENA_MAXIMA})
    if fora:
        raise ValueError(
            f"dezenas fora do intervalo de 01 a 25: {', '.join(map(str, fora))}"
        )
    repetidas = sorted({d for d in dezenas if dezenas.count(d) > 1})
    if repetidas:
        raise ValueError(f"dezenas repetidas: {', '.join(f'{d:02d}' for d in repetidas)}")
    if not minimo <= len(dezenas) <= maximo:
        esperado = str(minimo) if minimo == maximo else f"de {minimo} a {maximo}"
        raise ValueError(f"são necessárias {esperado} dezenas; foram informadas {len(dezenas)}")
    return sorted(dezenas)


class ConcursoEntrada(BaseModel):
    numero: int = Field(gt=0)
    data_sorteio: date
    dezenas: list[int]

    @field_validator("dezenas")
    @classmethod
    def _validar_dezenas(cls, dezenas: list[int]) -> list[int]:
        return normalizar_dezenas(dezenas, DEZENAS_POR_RESULTADO, DEZENAS_POR_RESULTADO)


class ConcursoSaida(ConcursoEntrada):
    model_config = ConfigDict(from_attributes=True)

    id: int
