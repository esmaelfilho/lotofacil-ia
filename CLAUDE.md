# CLAUDE.md

Orientações para quem (pessoa ou agente) trabalhar neste repositório. Responda e documente
em português.

## Projeto

Sistema de estatísticas e geração de jogos da Lotofácil. Fase atual: base do backend pronta
(Fase 1 do backlog). Leia `docs/REQUISITOS.md`, `docs/ARQUITETURA.md` e `docs/BANCO_DE_DADOS.md`
antes de propor mudanças.

## Regras obrigatórias

- **Banco:** PostgreSQL é o único banco, em desenvolvimento, testes e produção (ADR-001).
  Não introduza SQLite, `sqlite:///`, arquivos `.db` ou fallback para outro banco.
- **Acesso a dados:** SQLAlchemy 2.x no estilo 2.0 (`Mapped`, `select()`), driver Psycopg 3
  (`postgresql+psycopg://`).
- **Esquema:** toda alteração estrutural é uma migração Alembic. Nunca use
  `Base.metadata.create_all()` fora de experimentos descartáveis. Revise todo autogenerate;
  funções SQL e alguns `CHECK` precisam de `op.execute()`.
- **Dezenas:** `smallint[]` em ordem crescente, validadas por `lotofacil_dezenas_validas`
  (ADR-002). Normalize no backend antes de gravar. Nunca reconstrua um resultado a partir
  da ordem de retorno de linhas.
- **Estatísticas:** calcule a partir de `concursos` com SQL agregado nos serviços de
  `app/services/estatisticas/`. Não crie tabelas de pré-cálculo sem nova ADR com medição
  (ADR-003).
- **Configuração:** somente por variáveis de ambiente (`DATABASE_URL`, `TEST_DATABASE_URL`).
  Nunca grave senha real em código, documentação ou commit. `.env` não é versionado.
- **Logs:** nunca registre a URL de conexão com senha; use
  `render_as_string(hide_password=True)`.
- **Testes:** integração em PostgreSQL real, no banco `*_test` (veja
  `docs/PLANO_DE_TESTES.md`). Nunca rode testes contra o banco de desenvolvimento. Não
  declare testes aprovados sem executá-los e mostrar a saída real. Não desative testes para
  fazer a suíte passar.
- **Escopo:** não implemente login, multiusuário ou outras funcionalidades futuras sem
  pedido explícito.
- **Documentação:** ao mudar comportamento, atualize os documentos de `docs/` e o
  `docs/CHANGELOG.md`. Decisões arquiteturais novas vão para `docs/DECISOES.md`. Não apague
  requisitos ou decisões; marque-os como substituídos.

## Comandos

```bash
cd backend && alembic upgrade head          # aplicar migrações
cd backend && alembic revision --autogenerate -m "descricao"   # nova migração (revisar!)
cd backend && pytest                         # testes (exige TEST_DATABASE_URL)
cd backend && uvicorn app.main:app --reload  # API
cd frontend && npm run dev                   # interface
cd frontend && npm run test                  # Vitest
```

## Instruções obsoletas

Qualquer instrução anterior que mencione SQLite, criação automática de tabelas ou banco
em arquivo local está substituída pela ADR-001.
