"""Modelos SQLAlchemy. Importar este pacote registra todas as tabelas em Base.metadata."""

from app.models.concurso import Concurso
from app.models.estrategia import Estrategia, EstrategiaRegra, RegraEstatistica
from app.models.geracao import Avaliacao, GeracaoJogos, JogoGerado
from app.models.importacao import HistoricoImportacao

__all__ = [
    "Avaliacao",
    "Concurso",
    "Estrategia",
    "EstrategiaRegra",
    "GeracaoJogos",
    "HistoricoImportacao",
    "JogoGerado",
    "RegraEstatistica",
]
