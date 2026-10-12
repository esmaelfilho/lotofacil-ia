"""Cliente da API de resultados das Loterias Caixa (Lotofácil).

A API é a mesma usada pelo site de loterias da Caixa, mas não é documentada oficialmente:
o formato pode mudar. Todo dado recebido é validado antes de ser usado.

Endereços usados:
- GET {base}            -> último concurso
- GET {base}/{numero}   -> concurso específico
"""

import json
import logging
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.schemas.concurso import DEZENAS_POR_RESULTADO, normalizar_dezenas

log = logging.getLogger("lotofacil.caixa")

URL_PADRAO = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
CABECALHOS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Lotofacil-IA; uso pessoal)",
}

BuscarJson = Callable[[str], Any]


class ErroFonteExterna(Exception):
    """A API da Caixa não respondeu ou respondeu algo inesperado."""


class ConcursoNaoEncontrado(ErroFonteExterna):
    """A API respondeu que o concurso pedido não existe."""


class DadosInvalidosCaixa(ErroFonteExterna):
    """A API respondeu, mas o concurso veio com dados inválidos (ele é rejeitado)."""


@dataclass(frozen=True)
class ResultadoCaixa:
    numero: int
    data_sorteio: date
    dezenas: list[int]


def converter_resultado(dados: Any) -> ResultadoCaixa:
    """Converte o JSON da Caixa num resultado validado (15 dezenas distintas de 1 a 25)."""
    if not isinstance(dados, dict):
        raise ErroFonteExterna("a API da Caixa não devolveu um objeto JSON")
    try:
        numero = int(dados["numero"])
        data_sorteio = datetime.strptime(str(dados["dataApuracao"]), "%d/%m/%Y").date()
        dezenas = [int(d) for d in dados["listaDezenas"]]
    except KeyError as erro:
        raise ErroFonteExterna(
            f"a resposta da API da Caixa não tem o campo {erro}; o formato pode ter mudado"
        ) from None
    except (TypeError, ValueError) as erro:
        raise DadosInvalidosCaixa(
            f"valor inesperado na resposta da API da Caixa: {erro}"
        ) from None
    try:
        dezenas = normalizar_dezenas(dezenas, DEZENAS_POR_RESULTADO, DEZENAS_POR_RESULTADO)
    except ValueError as erro:
        raise DadosInvalidosCaixa(f"concurso {numero} com dezenas inválidas: {erro}") from None
    return ResultadoCaixa(numero=numero, data_sorteio=data_sorteio, dezenas=dezenas)


def buscar_json_http(url: str, timeout: float = 15.0) -> Any:
    """GET simples com a biblioteca padrão. Usa os certificados e o proxy do sistema."""
    requisicao = urllib.request.Request(url, headers=CABECALHOS)
    contexto = ssl.create_default_context()
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout, context=contexto) as resposta:
            corpo = resposta.read()
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            raise ConcursoNaoEncontrado(f"a API da Caixa respondeu 404 para {url}") from None
        raise ErroFonteExterna(f"a API da Caixa respondeu com erro HTTP {erro.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        motivo = getattr(erro, "reason", erro)
        raise ErroFonteExterna(
            f"não foi possível acessar a API da Caixa ({motivo}). Confira a internet ou o proxy."
        ) from None
    try:
        return json.loads(corpo)
    except ValueError:
        raise ErroFonteExterna(
            "a API da Caixa não respondeu em JSON (pode estar fora do ar ou bloqueando o acesso)"
        ) from None


class ClienteCaixa:
    def __init__(
        self,
        url_base: str = URL_PADRAO,
        buscar: BuscarJson | None = None,
        pausa_segundos: float = 0.3,
        tentativas: int = 3,
        timeout_segundos: float = 15.0,
    ) -> None:
        self.url_base = url_base.rstrip("/")
        self._buscar = buscar or (lambda url: buscar_json_http(url, timeout_segundos))
        self.pausa_segundos = pausa_segundos
        self.tentativas = tentativas
        self._ultima_chamada = 0.0

    def _get(self, url: str) -> Any:
        for tentativa in range(1, self.tentativas + 1):
            espera = self.pausa_segundos - (time.monotonic() - self._ultima_chamada)
            if espera > 0:
                time.sleep(espera)
            self._ultima_chamada = time.monotonic()
            try:
                return self._buscar(url)
            except (ConcursoNaoEncontrado, DadosInvalidosCaixa):
                raise
            except ErroFonteExterna as erro:
                if tentativa == self.tentativas:
                    raise
                log.warning("Tentativa %s falhou (%s); tentando de novo.", tentativa, erro)
                time.sleep(self.pausa_segundos * 2 * tentativa)
        raise AssertionError("inalcançável")

    def ultimo_concurso(self) -> ResultadoCaixa:
        return converter_resultado(self._get(self.url_base))

    def concurso(self, numero: int) -> ResultadoCaixa:
        resultado = converter_resultado(self._get(f"{self.url_base}/{numero}"))
        if resultado.numero != numero:
            raise DadosInvalidosCaixa(
                f"pedimos o concurso {numero}, mas a API devolveu o {resultado.numero}"
            )
        return resultado
