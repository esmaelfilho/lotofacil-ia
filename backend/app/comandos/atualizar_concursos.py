"""Atualiza os concursos pela linha de comando, mostrando o progresso.

Útil para a primeira carga, que busca milhares de concursos:

    python -m app.comandos.atualizar_concursos
"""

import sys

from app.core.config import ConfiguracaoInvalida, carregar_configuracoes
from app.core.logging import configurar_logs
from app.db.session import criar_engine, criar_fabrica_de_sessoes
from app.db.verificacao import ErroDeConexao, verificar_conexao
from app.integracoes.caixa import ClienteCaixa, ErroFonteExterna
from app.services.atualizacao import atualizar_concursos


def main() -> int:
    configurar_logs("WARNING")
    try:
        cfg = carregar_configuracoes()
        engine = criar_engine(cfg.url_banco, connect_timeout=cfg.database_connect_timeout)
        verificar_conexao(engine)
    except (ConfiguracaoInvalida, ErroDeConexao) as erro:
        print(erro, file=sys.stderr)
        return 1

    cliente = ClienteCaixa(
        url_base=cfg.caixa_api_url,
        pausa_segundos=cfg.caixa_pausa_segundos,
        timeout_segundos=cfg.caixa_timeout_segundos,
    )

    def mostrar(feitos: int, total: int) -> None:
        print(f"  {feitos} de {total} concursos processados", flush=True)

    print("Consultando a API da Caixa...", flush=True)
    try:
        with criar_fabrica_de_sessoes(engine)() as sessao:
            resumo = atualizar_concursos(sessao, cliente, ao_progredir=mostrar)
    except ErroFonteExterna as erro:
        print(f"Não foi possível consultar a Caixa: {erro}", file=sys.stderr)
        return 2
    finally:
        engine.dispose()

    print()
    print(resumo.mensagem)
    print(
        f"Inseridos: {resumo.inseridos}  Ignorados: {resumo.ignorados}  "
        f"Rejeitados: {resumo.rejeitados}  Último no banco: {resumo.ultimo_concurso_banco}"
    )
    return 0 if resumo.status in ("CONCLUIDA", "CONCLUIDA_COM_REJEICOES") else 3


if __name__ == "__main__":
    sys.exit(main())
