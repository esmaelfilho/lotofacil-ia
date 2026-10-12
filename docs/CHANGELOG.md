# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado
- Atualização dos concursos pela API de resultados da Caixa (ADR-004): busca só os que
  faltam, grava em lotes com `ON CONFLICT`, registra em `historico_importacoes` e continua de
  onde parou após falhas. Endpoints `POST /concursos/atualizar`, `GET /concursos`,
  `GET /concursos/{numero}`, `GET /importacoes` e comando `app.comandos.atualizar_concursos`.
- Migração `0002`: `historico_importacoes.status` passa a `varchar(30)` (a situação
  `CONCLUIDA_COM_REJEICOES` não cabia em 20 caracteres).
- Base do backend (Fase 1): configuração por `.env` com validação e mensagens de erro úteis,
  filtro que remove senhas dos logs, engine SQLAlchemy com Psycopg 3, modelos das 8 tabelas,
  migração Alembic `0001` (função `lotofacil_dezenas_validas` e tabelas), endpoint
  `GET /saude` e testes pytest (unitários e de integração em PostgreSQL, com trava que exige
  banco `*_test`). Mensagens de erro de conexão reconhecem o PostgreSQL em português.
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
