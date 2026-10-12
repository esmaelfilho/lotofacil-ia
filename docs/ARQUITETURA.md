# Arquitetura

## 1. Visão geral

```
[ Navegador ]
     │  React + TypeScript + Vite + Material UI + Recharts
     ▼
[ API REST — FastAPI + Pydantic ]
     │  routers → services → repositories
     ▼
[ SQLAlchemy 2.x (ORM) + Psycopg 3 ]
     ▼
[ PostgreSQL ]  ← esquema versionado pelo Alembic
```

PostgreSQL é o único banco oficial, em desenvolvimento, testes e produção (ADR-001).

## 2. Estrutura de pastas prevista

```
lotofacil-ia/
├── backend/
│   ├── alembic.ini
│   ├── migrations/              # Alembic (env.py, script.py.mako, versions/)
│   ├── app/
│   │   ├── main.py              # cria o FastAPI; lifespan valida config e conexão
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings), lê DATABASE_URL
│   │   │   └── logging.py       # configuração de logs, sem credenciais
│   │   ├── db/
│   │   │   ├── base.py          # DeclarativeBase + naming_convention
│   │   │   ├── session.py       # engine, sessionmaker, dependência get_session
│   │   │   └── verificacao.py   # verificar_conexao() na inicialização
│   │   ├── models/              # modelos SQLAlchemy, agrupados por assunto
│   │   ├── schemas/             # modelos Pydantic de entrada e saída
│   │   ├── repositories/        # acesso a dados
│   │   ├── services/
│   │   │   ├── estatisticas/    # frequencia, atraso, perfil, combinacoes...
│   │   │   ├── importacao.py
│   │   │   ├── geracao.py
│   │   │   └── avaliacao.py
│   │   └── api/routers/         # concursos, estatisticas, estrategias, geracoes...
│   ├── tests/
│   │   ├── unit/                # sem banco
│   │   └── integration/         # PostgreSQL de teste
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   └── package.json
├── docs/
├── .env.example
└── README.md
```

## 3. Backend

- **Camadas:** routers só tratam HTTP; services têm as regras; repositories fazem o acesso
  a dados. Services recebem a `Session` por injeção de dependência.
- **Transações:** uma sessão por requisição (`get_session`). O service define o limite da
  transação com `with session.begin():`; erros causam `ROLLBACK` automático.
- **Erros do banco:** `IntegrityError` é traduzido em respostas 409 (duplicado, uso em
  `RESTRICT`) ou 422 (violação de `CHECK`) com mensagens em português; `OperationalError`
  vira 503.
- **Validação:** Pydantic valida dezenas (15 distintas, 1 a 25, ordenadas na
  normalização) antes de chegar ao banco. O banco repete a regra como última barreira.

### Configuração e conexão

- `app/core/config.py` define `Settings` com `pydantic-settings`, lendo variáveis de ambiente
  e, em desenvolvimento, o arquivo `.env`.
- `DATABASE_URL` é obrigatória e deve usar o esquema `postgresql+psycopg://`. Uma URL
  `sqlite://`, ausente ou malformada interrompe a inicialização com mensagem explicando o
  formato esperado.
- O `lifespan` do FastAPI executa `SELECT 1` com tempo limite (`DATABASE_CONNECT_TIMEOUT`).
  Em falha, a mensagem informa host, porta, banco e a causa provável (servidor
  indisponível, autenticação recusada, banco inexistente) e encerra o processo.
- A URL é sempre registrada com `url.render_as_string(hide_password=True)`; a senha nunca
  aparece em log, exceção ou resposta da API.
- O engine usa `pool_pre_ping=True` e `pool_size` configurável.
- O lifespan também verifica se o banco está na última revisão do Alembic e avisa quando
  houver migrações pendentes; ele **não** as aplica automaticamente.

### Estatísticas

`app/services/estatisticas/` agrupa os cálculos por tema (frequência e janelas, atraso,
perfil do concurso, linhas e colunas, sequências, repetição, combinações). Cada serviço
executa consultas SQL agregadas (veja `BANCO_DE_DADOS.md`, seção 6) e devolve modelos
Pydantic. Cálculos sobre um jogo isolado (ex.: perfil de um jogo gerado) usam funções Python
puras compartilhadas, testadas sem banco, com as mesmas definições do SQL.

Não há tabelas de pré-cálculo (ADR-003).

## 4. Frontend

React + TypeScript com Vite, componentes Material UI e gráficos Recharts. Consome a API
pela variável `VITE_API_URL`. Não acessa o banco diretamente. O aviso sobre a independência
dos sorteios aparece nas telas de estatística e de geração.

## 5. Ambientes

| Ambiente | Banco | Esquema |
|---|---|---|
| Desenvolvimento | PostgreSQL local ou contêiner, banco `lotofacil` | `alembic upgrade head` |
| Testes | PostgreSQL, banco separado terminado em `_test` | criado pelos testes via Alembic |
| Produção | PostgreSQL gerenciado ou servidor dedicado | `alembic upgrade head` no deploy, antes de iniciar a aplicação |

## 6. Segurança

- Sem credenciais no repositório; `.env` está no `.gitignore`.
- Usuário do banco da aplicação sem privilégio de superusuário.
- Login e multiusuário estão fora do escopo desta versão.
