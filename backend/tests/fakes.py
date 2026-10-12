"""API da Caixa simulada para os testes (nenhum teste acessa a internet)."""

import json
from pathlib import Path

from app.integracoes.caixa import ClienteCaixa, ConcursoNaoEncontrado, ErroFonteExterna

EXEMPLO_REAL = json.loads(
    (Path(__file__).parent / "dados" / "caixa_lotofacil_3802.json").read_text(encoding="utf-8")
)
URL = "https://caixa.exemplo/api/lotofacil"


def resposta(numero: int, dezenas: list[int] | None = None) -> dict:
    """Resposta no formato real da Caixa, com dezenas determinísticas por número."""
    if dezenas is None:
        inicio = numero % 11  # 0..10 -> 15 dezenas consecutivas dentro de 1..25
        dezenas = list(range(inicio + 1, inicio + 16))
    dados = dict(EXEMPLO_REAL)
    dados.update(
        numero=numero,
        dataApuracao=f"{(numero % 28) + 1:02d}/{(numero % 12) + 1:02d}/2020",
        listaDezenas=[f"{d:02d}" for d in sorted(dezenas)],
    )
    return dados


class CaixaFalsa:
    """Responde como a Caixa até `ultimo`; permite simular erros por número."""

    def __init__(self, ultimo: int, falhar_em: int | None = None, invalidos=(), inexistentes=()):
        self.ultimo = ultimo
        self.falhar_em = falhar_em
        self.invalidos = set(invalidos)
        self.inexistentes = set(inexistentes)
        self.pedidos: list[str] = []

    def __call__(self, url: str) -> dict:
        self.pedidos.append(url)
        sufixo = url.removeprefix(URL).strip("/")
        numero = int(sufixo) if sufixo else self.ultimo
        if numero == self.falhar_em:
            raise ErroFonteExterna("tempo esgotado (simulado)")
        if numero in self.inexistentes or numero > self.ultimo:
            raise ConcursoNaoEncontrado(f"404 para {url}")
        if numero in self.invalidos:
            return resposta(numero, dezenas=list(range(1, 15)))  # só 14 dezenas
        return resposta(numero)

    def cliente(self) -> ClienteCaixa:
        return ClienteCaixa(url_base=URL, buscar=self, pausa_segundos=0, tentativas=2)
