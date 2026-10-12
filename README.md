# Lotofácil IA

Sistema de análise estatística e geração de jogos da **Lotofácil**.

> Cada sorteio é independente. As estatísticas descrevem resultados passados e não
> aumentam a chance de acerto.

**Situação:** a base do backend está pronta (configuração, conexão com o PostgreSQL,
modelos, migração inicial, endpoint `/saude` e testes). Importação, estatísticas, geração de
jogos e o frontend ainda serão feitos (veja [`docs/BACKLOG.md`](docs/BACKLOG.md)).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Banco de dados | **PostgreSQL** 15 ou superior (o projeto usa a 18), oficial em todos os ambientes |
| Acesso a dados | SQLAlchemy 2.x, Psycopg 3, Alembic |
| Backend | Python 3.12 a 3.14, FastAPI, Pydantic |
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

1. Instale o PostgreSQL 18 (ou use um contêiner, veja
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

## Executar o backend

No Windows (PowerShell), a partir da raiz do projeto:

```powershell
cd backend
python -m venv .venv                 # cria o ambiente virtual (só na primeira vez)
.\.venv\Scripts\Activate.ps1         # ativa o ambiente (toda vez que abrir o terminal)
python -m pip install -e ".[dev]"    # instala as dependências (primeira vez ou quando mudarem)
alembic upgrade head                 # cria/atualiza as tabelas no banco
uvicorn app.main:app --reload        # inicia a API: http://localhost:8000/docs
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate`.

Se o PowerShell recusar o `Activate.ps1` por política de execução, rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Para conferir: http://localhost:8000/saude deve responder `"status": "ok"` e
`"banco": "conectado"`.

O frontend (React) ainda não foi criado; quando existir:

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

A aplicação não cria tabelas sozinha: sempre rode `alembic upgrade head` depois de
atualizar o código. Se não conseguir conectar ao banco, ela encerra com uma mensagem
indicando host, porta, banco e a causa provável, sem mostrar a senha.

## Testes

```powershell
cd backend
pytest                               # unitários + integração (usa TEST_DATABASE_URL, banco *_test)
pytest -m "not integration"          # só os que não usam banco
```

Os testes se recusam a rodar contra um banco cujo nome não termine em `_test`.
