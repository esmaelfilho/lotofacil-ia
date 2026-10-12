# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado
- Especificação inicial: `README.md`, `CLAUDE.md`, `docs/REQUISITOS.md`,
  `docs/ARQUITETURA.md`, `docs/BANCO_DE_DADOS.md`, `docs/PLANO_DE_TESTES.md`,
  `docs/BACKLOG.md`, `docs/DECISOES.md`.
- `.env.example` com valores demonstrativos e `.gitignore` excluindo `.env`.
- ADR-001: PostgreSQL como banco oficial desde a primeira versão, com SQLAlchemy 2.x,
  Psycopg 3 e Alembic.
- ADR-002: dezenas armazenadas em `smallint[]` ordenado, validadas por `CHECK`.
- ADR-003: estatísticas calculadas sob demanda, sem tabelas de pré-cálculo.
- Esquema de referência para concursos, regras estatísticas, estratégias, gerações, jogos
  gerados, avaliações e histórico de importações, validado num PostgreSQL 16.

### Alterado
- O banco previsto deixou de ser SQLite e passou a ser PostgreSQL em todos os ambientes.

### Removido
- SQLite como banco oficial ou padrão de desenvolvimento.
