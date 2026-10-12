# Lotofácil IA

Sistema de análise estatística e geração de jogos da **Lotofácil**.

> Cada sorteio é independente. As estatísticas descrevem resultados passados e não
> aumentam a chance de acerto.

**Situação:** fase de especificação. Ainda não há código; os comandos de execução abaixo
descrevem como o projeto vai funcionar quando o backend e o frontend forem criados (veja
[`docs/BACKLOG.md`](docs/BACKLOG.md)).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Banco de dados | **PostgreSQL** 15+ (recomendado 16), oficial em todos os ambientes |
| Acesso a dados | SQLAlchemy 2.x, Psycopg 3, Alembic |
| Backend | Python 3.12+, FastAPI, Pydantic |
| Frontend | React, TypeScript, Vite, Material UI, Recharts |
| Testes | pytest (backend, integração em PostgreSQL), Vitest (frontend) |

SQLite não é usado em nenhum ambiente ([ADR-001](docs/DECISOES.md)).

## Documentação

- [Requisitos](docs/REQUISITOS.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Banco de dados](docs/BANCO_DE_DADOS.md)
- [Plano de testes](docs/PLANO_DE_TESTES.md)
- [Backlog](docs/BACKLOG.md)
- [Decisões](docs/DECISOES.md)
- [Changelog](docs/CHANGELOG.md)

## Preparar o PostgreSQL

1. Instale o PostgreSQL 16 (ou use um contêiner, veja
   [`docs/BANCO_DE_DADOS.md`](docs/BANCO_DE_DADOS.md#1-bancos-e-usuários)).
2. Crie o usuário da aplicação e os bancos de desenvolvimento e de teste:

   ```bash
   psql -U postgres -v senha='<escolha-uma-senha>' <<'SQL'
   CREATE ROLE lotofacil_app LOGIN PASSWORD :'senha';
   CREATE DATABASE lotofacil      OWNER lotofacil_app ENCODING 'UTF8' TEMPLATE template0;
   CREATE DATABASE lotofacil_test OWNER lotofacil_app ENCODING 'UTF8' TEMPLATE template0;
   SQL
   ```

3. Copie `.env.example` para `.env` e preencha `DATABASE_URL` e `TEST_DATABASE_URL`.
   O arquivo `.env` não é versionado.

```
DATABASE_URL=postgresql+psycopg://lotofacil_app:<senha>@localhost:5432/lotofacil
TEST_DATABASE_URL=postgresql+psycopg://lotofacil_app:<senha>@localhost:5432/lotofacil_test
```

## Executar (quando o código existir)

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head               # cria/atualiza o esquema
uvicorn app.main:app --reload      # http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

A aplicação não cria tabelas sozinha: sempre rode `alembic upgrade head` depois de
atualizar o código. Se não conseguir conectar ao banco, ela encerra com uma mensagem
indicando host, porta, banco e a causa provável, sem mostrar a senha.

## Testes

```bash
cd backend && pytest               # integração usa TEST_DATABASE_URL (banco *_test)
cd frontend && npm run test
```

Os testes se recusam a rodar contra um banco cujo nome não termine em `_test`.
