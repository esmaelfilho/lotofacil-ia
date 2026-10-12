# Backlog

Itens em ordem de prioridade. Estado: `[ ]` a fazer, `[~]` em andamento, `[x]` feito.

## Fase 0 — Especificação
- [x] Definir PostgreSQL como banco oficial desde a primeira versão (ADR-001).
- [x] Definir representação das dezenas e esquema inicial (ADR-002, `BANCO_DE_DADOS.md`).
- [x] Definir estratégia de estatísticas sem pré-cálculo (ADR-003).
- [x] Criar `.env.example` e `.gitignore` com `.env`.

## Fase 1 — Fundação do backend
- [ ] Criar `backend/` com `pyproject.toml` (FastAPI, Pydantic, pydantic-settings,
      SQLAlchemy 2.x, Alembic, psycopg[binary] 3, pytest).
- [ ] `core/config.py`: leitura e validação de `DATABASE_URL` (somente `postgresql+psycopg`).
- [ ] `db/session.py` e verificação de conexão no `lifespan`, com mensagens úteis e sem
      credenciais nos logs.
- [ ] Configurar Alembic (`env.py` lendo a URL das `Settings`, `naming_convention`).
- [ ] Migração inicial com a função `lotofacil_dezenas_validas` e as tabelas do esquema de
      referência.
- [ ] Fixtures de teste com banco `_test`, trava de segurança e savepoints.
- [ ] Testes T01, T02, T05 e T09.
- [ ] `docker-compose.yml` opcional só com o PostgreSQL de desenvolvimento e de teste.

## Fase 2 — Concursos e importação
- [ ] CRUD de concursos (T03, T04).
- [ ] Importação idempotente com histórico (T07, T08).
- [ ] Definir o formato do arquivo de importação (planilha oficial da Caixa ou CSV próprio).

## Fase 3 — Estatísticas
- [ ] Serviços de estatística (RF-03.1 a RF-03.13) e endpoints.
- [ ] Testes T06 com conjunto de concursos de valores conhecidos.

## Fase 4 — Regras, estratégias, geração e avaliação
- [ ] Carga inicial de `regras_estatisticas` por migração de dados.
- [ ] CRUD de estratégias.
- [ ] Geração de jogos reproduzível (semente + cópia dos parâmetros).
- [ ] Avaliação de jogos e conferência contra o histórico.

## Fase 5 — Frontend
- [ ] Projeto Vite + React + TypeScript + Material UI + Recharts.
- [ ] Telas de concursos, estatísticas, estratégias, geração e avaliação.
- [ ] Testes com Vitest.

## Ideias futuras (fora do escopo atual)
- [ ] Guardar a ordem em que as dezenas foram sorteadas (coluna adicional, se a fonte
      oferecer).
- [ ] Histórico de prêmios e acumulações.
- [ ] *Materialized views* para estatísticas lentas, se medições justificarem (ADR-003).
- [ ] Login e multiusuário (não implementar agora).
