# Lotofácil IA

Sistema de análise estatística e geração de jogos da **Lotofácil**.

> Cada sorteio é independente. As estatísticas descrevem resultados passados e não
> aumentam a chance de acerto.

**Situação:** a base do backend está pronta (configuração, conexão com o PostgreSQL,
modelos, migrações, endpoint `/saude` e testes) e os concursos já podem ser atualizados pela
API da Caixa, consultados nas estatísticas e usados para gerar e conferir jogos, pela API ou pela tela no navegador. Próximos passos (veja [`docs/BACKLOG.md`](docs/BACKLOG.md)).

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

## Executar a tela (frontend)

Precisa do **Node.js 24 LTS** (https://nodejs.org). Com o backend rodando em outro
PowerShell:

```powershell
cd frontend
npm install                          # baixa as bibliotecas (primeira vez ou quando mudarem)
npm run dev                          # abre a tela: http://localhost:5173
```

A tela chama `/api/...` e o Vite repassa para o backend em `VITE_API_URL` (padrão
`http://localhost:8000`), lido do `.env` da raiz ([ADR-006](docs/DECISOES.md)). Abas:
**Concursos** (botão "Atualizar concursos", último resultado, lista e histórico),
**Estatísticas** (gráficos, quentes e frias, pares e trios, volante de obrigatórias e
excluídas), **Perfil dos concursos**, **Jogos** (estratégias, geração, gravação e
conferência) e **Testar estratégia** (como os jogos de cada estratégia teriam se saído num
concurso que já saiu).

A aplicação não cria tabelas sozinha: sempre rode `alembic upgrade head` depois de
atualizar o código. Se não conseguir conectar ao banco, ela encerra com uma mensagem
indicando host, porta, banco e a causa provável, sem mostrar a senha.

## Atualizar os concursos

Os resultados vêm da API de resultados da Caixa ([ADR-004](docs/DECISOES.md)). São buscados
somente os concursos que ainda não estão no banco.

```powershell
cd backend
python -m app.comandos.atualizar_concursos   # primeira carga (milhares de concursos), com progresso
```

Depois, para buscar os novos, use `POST /concursos/atualizar` em http://localhost:8000/docs
(ou rode o comando de novo). Pode repetir à vontade: nada é duplicado.

## Estatísticas

Com a API rodando, abra http://localhost:8000/docs, seção **estatísticas**. Todas só consultam
o banco:

| Endpoint | O que mostra |
|---|---|
| `GET /estatisticas/frequencia` | Vezes que cada dezena saiu, no total e nos últimos 10, 50 e 100 concursos |
| `GET /estatisticas/quentes-frias` | As dezenas que mais e menos saíram numa janela (padrão: 5 dezenas, últimos 50) |
| `GET /estatisticas/atrasos` | Há quantos concursos cada dezena não sai e o maior atraso que já teve |
| `GET /estatisticas/perfil` | Perfil de cada concurso: pares/ímpares, primos, soma, moldura/miolo, linhas, colunas, sequências, Fibonacci, múltiplos de 3, repetidas do anterior |
| `GET /estatisticas/distribuicao` | Em quantos concursos cada valor de uma característica aconteceu (ex.: 7 pares, 8 pares...) |
| `GET /estatisticas/obrigatorias-excluidas` | Em quantos concursos todas as obrigatórias saíram e nenhuma excluída saiu |
| `GET /estatisticas/combinacoes` | Pares (`tamanho=2`) ou trios (`tamanho=3`) que mais saíram juntos |

Os endpoints de distribuição, obrigatórias/excluídas e combinações aceitam `ultimos=N` para
olhar só os últimos N concursos.

## Gerar e conferir jogos

> Gerar jogos com filtros estatísticos não aumenta a chance de acerto: todas as combinações
> têm a mesma chance em cada sorteio.

Na aba **Jogos** (ou pela API, seção **jogos** e **estratégias** do `/docs`):

| Endpoint | O que faz |
|---|---|
| `GET /regras` | Catálogo de regras (pares, primos, soma, moldura, miolo, maior sequência, Fibonacci, múltiplos de 3, repetidas do concurso base), cada uma com faixa padrão |
| `GET/POST /estrategias`, `GET/PUT /estrategias/{id}` | Estratégias: conjuntos de regras com mínimo e máximo |
| `POST /estrategias/{id}/desativar` e `/ativar`, `DELETE /estrategias/{id}` | Uma estratégia já usada só pode ser desativada |
| `POST /geracoes` | Gera de 1 a 100 jogos de 15 a 20 dezenas, com estratégia, obrigatórias e excluídas; a mesma `semente` reproduz os mesmos jogos. Com `"gravar": false`, só mostra os jogos, sem gravar |
| `GET /geracoes`, `GET /geracoes/{id}` | Gerações feitas e seus jogos |
| `POST /geracoes/{id}/conferir?concurso=N` | Confere os jogos contra um concurso e registra os acertos |
| `POST /jogos/conferir-historico` | Quantas vezes um jogo teria feito 11 a 15 pontos em todo o histórico |
| `POST /testes-estrategia` | Testa estratégias num concurso que já saiu (veja abaixo) |

Na tela, "Gerar jogos" mostra os jogos sem gravar. Clique em **Gravar jogos** para guardá-los
(são gravados exatamente os jogos mostrados) e conferi-los depois em "Jogos gravados".

### Testar estratégia

Na aba **Testar estratégia**, escolha um concurso que já saiu e uma ou mais estratégias (e,
para comparar, jogos sem estratégia). Os jogos são gerados como se fosse a véspera, com base
no concurso anterior, e conferidos com o resultado: as dezenas acertadas aparecem em verde e
um resumo mostra o maior acerto, a média e quantos jogos fizeram 11 a 15 pontos. Nada é
gravado, a não ser que você clique em **Gravar estes jogos**; aí eles vão para "Jogos
gravados" já conferidos com o concurso testado.

O catálogo de regras é criado pela migração `0003`: rode `alembic upgrade head` depois de
atualizar o código.

## Testes

```powershell
cd backend
pytest                               # unitários + integração (usa TEST_DATABASE_URL, banco *_test)
pytest -m "not integration"          # só os que não usam banco

cd ..\frontend
npm run test                         # Vitest (API simulada, não precisa do backend)
npm run build                        # confere os tipos do TypeScript e gera a versão final
```

Os testes se recusam a rodar contra um banco cujo nome não termine em `_test`.
