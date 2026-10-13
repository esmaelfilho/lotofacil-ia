# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado
- Testar estratégia (RF-07, ADR-008): nova aba em que se escolhe um concurso que já saiu e uma
  ou mais estratégias (e jogos aleatórios, para comparar); os jogos são gerados com base no
  concurso anterior e conferidos com o resultado, com resumo de maior acerto, média e 11 a 15
  pontos. Endpoint `POST /testes-estrategia`. Os jogos de uma estratégia podem ser gravados e
  já ficam conferidos. Nenhuma tabela nova e nenhuma migração.
- Estratégias, geração e conferência de jogos (Fase 4, RF-04 a RF-06): catálogo de 9 regras de
  faixa (migração de dados `0003`), CRUD de estratégias, geração reproduzível por semente com
  cópia dos parâmetros (ADR-007), conferência contra um concurso (grava `avaliacoes`) e contra
  o histórico. Endpoints `/regras`, `/estrategias`, `/geracoes`, `/jogos/conferir-historico`.
  Aba **Jogos** na tela. Nenhuma tabela nova.
- Tela no navegador (`frontend/`, React + TypeScript + Vite + Material UI + Recharts): abas
  Concursos (botão "Atualizar concursos", último resultado, lista paginada, histórico),
  Estatísticas (frequência, quentes e frias, atrasos, distribuição, pares e trios, volante de
  obrigatórias e excluídas) e Perfil dos concursos. Proxy do Vite para a API (ADR-006).
  Testes Vitest. Backend sem alterações.
- Estatísticas (Fase 3, RF-03.1 a RF-03.13): endpoints `GET /estatisticas/frequencia`,
  `/quentes-frias`, `/atrasos`, `/perfil`, `/distribuicao`, `/obrigatorias-excluidas` e
  `/combinacoes`. Frequência, atraso e combinações em SQL; perfil dos concursos em Python
  (ADR-005). Sem migração e sem tabela nova (ADR-003).
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
- Gerar jogos na tela não grava mais automaticamente: os jogos aparecem como "não gravados"
  e o botão "Gravar jogos" grava exatamente esses jogos (RF-05.4). A lista "Jogos gerados"
  passou a se chamar "Jogos gravados". Na API, `POST /geracoes` ganhou o campo `gravar`
  (padrão `true`, como antes); com `false`, a resposta vem com `gravada: false` e sem `id`.
- O banco previsto deixou de ser SQLite e passou a ser PostgreSQL em todos os ambientes.

### Removido
- SQLite como banco oficial ou padrão de desenvolvimento.
