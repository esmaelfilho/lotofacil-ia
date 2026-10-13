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
│   │   ├── integracoes/
│   │   │   └── caixa.py         # cliente da API de resultados da Caixa
│   │   ├── comandos/
│   │   │   └── atualizar_concursos.py  # primeira carga pelo terminal, com progresso
│   │   ├── services/
│   │   │   ├── estatisticas/    # frequencia, atraso, perfil, combinacoes...
│   │   │   ├── atualizacao.py   # busca na Caixa os concursos que faltam e grava
│   │   │   ├── regras.py        # faixas aplicadas a um jogo (usa estatisticas/perfil.py)
│   │   │   ├── estrategias.py
│   │   │   ├── geracao.py       # sorteio com filtro, semente, cópia dos parâmetros
│   │   │   ├── avaliacao.py     # conferência contra um concurso e contra o histórico
│   │   │   ├── teste_estrategia.py  # testa estratégias num concurso passado (base = anterior)
│   │   │   └── erros.py         # ErroDeNegocio (422), NaoEncontrado (404), Conflito (409)
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

### Estratégias, geração e conferência

- **Regras** (`services/regras.py`): cada regra é uma faixa (mínimo e máximo) sobre um valor do
  jogo calculado com `estatisticas/perfil.py`, a mesma definição das estatísticas. O catálogo
  (nomes e faixas padrão) está na tabela `regras_estatisticas`, carregada pela migração `0003`.
- **Geração** (`services/geracao.py`): sorteia combinações com `random.Random(semente)` e mantém
  só as que respeitam obrigatórias, excluídas e todas as faixas, sem repetir jogo (ADR-007).
  Até 100 jogos por geração e 100.000 tentativas; se não houver jogos suficientes, nada é
  gravado e a resposta explica. A geração grava uma cópia das regras usadas. Com
  `gravar: false`, a geração só devolve os jogos, sem gravar; enviar de novo os mesmos
  parâmetros com a semente e o concurso base devolvidos grava exatamente os mesmos jogos
  (ADR-008).
- **Teste de estratégia** (`services/teste_estrategia.py`): para um concurso que já saiu,
  gera os jogos de cada estratégia com base no concurso anterior (nunca no testado), usando
  o mesmo `sortear_jogos` e a mesma semente, e confere contra o resultado. Só consulta; nada
  é gravado (ADR-008).
- **Conferência** (`services/avaliacao.py`): contra um concurso grava `avaliacoes`; contra o
  histórico só consulta.
- Os serviços lançam `ErroDeNegocio`, `NaoEncontrado` e `Conflito`; os routers os traduzem em
  422, 404 e 409 (`app/api/erros.py`).

### Estatísticas

`app/services/estatisticas/` agrupa os cálculos por tema: `frequencia.py` (frequência,
janelas, quentes e frias), `atraso.py`, `combinacoes.py` (pares e trios), `filtros.py`
(obrigatórias e excluídas), `perfil.py` (perfil de uma lista de dezenas, funções puras) e
`distribuicao.py` (perfil de cada concurso e distribuição das características). Os serviços
devolvem modelos Pydantic (`app/schemas/estatisticas.py`) e os endpoints ficam em
`app/api/routers/estatisticas.py`.

Agregações sobre o histórico são consultas SQL (veja `BANCO_DE_DADOS.md`, seção 6). O perfil
é calculado em Python sobre as dezenas lidas, para que a mesma função sirva aos concursos e
aos jogos gerados (ADR-005).

Não há tabelas de pré-cálculo (ADR-003).

## 4. Frontend

React + TypeScript com Vite, componentes Material UI e gráficos Recharts. Não acessa o banco
diretamente. O aviso sobre a independência dos sorteios aparece no topo de todas as telas.

- **Conversa com a API:** a página chama sempre `/api/...`; em desenvolvimento o servidor do
  Vite repassa para `VITE_API_URL` (padrão `http://localhost:8000`, lida do `.env` da raiz,
  só variáveis `VITE_`). O backend não precisa de CORS (ADR-006).
- **Estrutura:** `src/api/` (cliente `fetch`, tipos das respostas, hook `useDados`),
  `src/componentes/` (bolinhas das dezenas, volante 5×5, gráfico de barras, seção, estados de
  carregando/erro), `src/paginas/` (Concursos, Estatísticas, Perfil, Jogos e Testar estratégia, com os
  componentes da aba Jogos em `src/paginas/jogos/`) e `src/util/`
  (formatação em português). Abas do Material UI, sem roteador.
- **Erros:** mensagens da API (`detail`) aparecem na tela; backend desligado mostra a
  orientação de iniciar o `uvicorn` e um botão "Tentar de novo".
- **Testes:** Vitest + Testing Library em jsdom, com `fetch` simulado
  (`src/testes/apiSimulada.ts`).

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
