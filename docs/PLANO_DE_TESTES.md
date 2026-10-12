# Plano de testes

## 1. Princípios

- Testes de integração do backend usam **PostgreSQL real**, para verificar migrações,
  restrições, transações e consultas como em produção. Não há SQLite em nenhum teste.
- Os testes nunca tocam o banco de desenvolvimento.
- Nenhum teste é declarado aprovado sem ter sido executado. Relatórios citam o comando e a
  saída real do pytest/Vitest.
- Testes não são desativados nem marcados como "skip" para fazer a suíte passar.

## 2. Isolamento do banco de testes

- Os testes usam apenas `TEST_DATABASE_URL`. `DATABASE_URL` é ignorada pela suíte.
- **Trava de segurança** na fixture de sessão: os testes se recusam a rodar se
  - `TEST_DATABASE_URL` não estiver definida;
  - o nome do banco não terminar em `_test`;
  - `TEST_DATABASE_URL` apontar para o mesmo banco que `DATABASE_URL`.
- No início da sessão de testes, o esquema é recriado do zero (`DROP SCHEMA public CASCADE;
  CREATE SCHEMA public;`) e as migrações são aplicadas com `alembic upgrade head`. Isso só é
  permitido depois da trava acima.
- Cada teste roda dentro de uma transação externa com `SAVEPOINT`
  (`join_transaction_mode="create_savepoint"`) e é desfeito ao final, deixando o banco limpo.
- Testes de transação que precisam de `COMMIT` real usam uma fixture própria que limpa as
  tabelas com `TRUNCATE ... RESTART IDENTITY CASCADE` ao final.
- Sem `TEST_DATABASE_URL`, os testes de integração são **ignorados com motivo explícito**
  (marcador `integration`), e o relatório informa que não foram executados.

## 3. Casos obrigatórios

| # | Área | Casos |
|---|---|---|
| T01 | Conexão e configuração | `DATABASE_URL` ausente, malformada ou `sqlite://` gera erro claro; servidor fora do ar gera erro útil; senha não aparece na mensagem nem nos logs (`caplog`) |
| T02 | Migrações | `upgrade head` a partir do banco vazio; `downgrade base` e novo `upgrade head`; nenhuma diferença entre modelos e banco após o upgrade (comparação do Alembic) |
| T03 | Concursos | inserir e consultar; leitura devolve as dezenas na ordem crescente gravada |
| T04 | Duplicidade | segundo concurso com o mesmo número gera `IntegrityError` no banco e 409 na API |
| T05 | Validação de resultados | 14 ou 16 dezenas, repetidas, 0, 26, `NULL`, fora de ordem: recusadas pelo Pydantic **e**, inseridas direto via SQL, pelo `CHECK` do banco |
| T06 | Estatísticas | resultados conferidos com um conjunto pequeno de concursos de valores conhecidos: frequência total e por janela, quentes/frias, atraso atual e maior atraso (incluindo dezena que nunca saiu e lacuna de numeração), pares/ímpares, primos, soma, moldura/miolo, linha/coluna, obrigatórias/excluídas, sequências, Fibonacci, múltiplos de 3, repetição, pares e trios |
| T07 | Importação idempotente | importar duas vezes o mesmo arquivo: segunda execução com 0 inseridos e N ignorados; divergência de dados é rejeitada e reportada sem sobrescrever |
| T08 | Transações e erros | falha no meio da importação desfaz os concursos inseridos e registra `FALHOU` com a mensagem; erro numa requisição não deixa sessão em estado inválido |
| T09 | Integridade dos relacionamentos | `RESTRICT` ao excluir concurso usado em geração ou avaliação; `CASCADE` de geração → jogos → avaliações; regra em uso não pode ser excluída; obrigatórias e excluídas não se sobrepõem |

Testes unitários (sem banco) cobrem as funções Python puras de estatística, os modelos
Pydantic e a montagem da mensagem de erro de conexão.

Frontend (Vitest): componentes de formulário de dezenas, exibição de estatísticas com dados
simulados e tratamento de erros da API.

## 4. Como executar

```bash
# backend (dentro de backend/, com o ambiente virtual ativo)
export TEST_DATABASE_URL=postgresql+psycopg://lotofacil_app:<senha>@localhost:5432/lotofacil_test
pytest                       # tudo
pytest -m "not integration"  # só unitários, sem banco

# frontend (dentro de frontend/)
npm run test
```

## 5. Situação atual

Fase 1 implementada. Execução em 2026-10-12, no ambiente de desenvolvimento do assistente
(Python 3.13, PostgreSQL 16, Linux), com `pytest`:

- **62 testes aprovados** (27 unitários + 35 de integração), 0 falhas.
- Cobertos: T01, T02, T05, T09 e a parte de banco de T03, T04 e T07 (`ON CONFLICT`).
- Travas verificadas: banco sem sufixo `_test` e `TEST_DATABASE_URL` igual a `DATABASE_URL`
  interrompem a suíte; sem `TEST_DATABASE_URL`, os 35 de integração são ignorados com motivo.
- Execução no ambiente do usuário (Windows, Python 3.14.8, PostgreSQL 18.6), 2026-10-12:
  **62 passed**. Dois ajustes vieram dessa execução: reconhecer mensagens do PostgreSQL em
  português com acentos corrompidos e aceitar "tempo esgotado" como causa de servidor
  indisponível no Windows.
- Fase 2 (atualização pela API da Caixa), 2026-10-12, no ambiente do assistente:
  **83 testes aprovados**. Cobrem T07 (primeira carga, segunda execução sem duplicar, lacunas,
  limite por execução) e T08 (falha no meio mantém os lotes gravados, registra `FALHOU` e a
  execução seguinte continua; rejeição de concurso inválido ou inexistente; Caixa fora do ar
  responde 502). A Caixa é simulada com o formato real da resposta; nenhum teste usa a
  internet. Esse teste revelou que `CONCLUIDA_COM_REJEICOES` não cabia na coluna `status`,
  corrigido pela migração `0002`.
  Execução no ambiente do usuário (Windows, Python 3.14.8, PostgreSQL 18.6), 2026-10-12:
  **83 passed**. Primeira carga real pela API da Caixa no mesmo dia: 3.802 concursos
  inseridos, 0 ignorados, 0 rejeitados.
- Fase 3 (estatísticas), 2026-10-12, no ambiente do assistente: **111 testes aprovados**.
  T06 coberto de duas formas: um conjunto de 4 concursos com lacuna na numeração e uma dezena
  que nunca saiu, com valores conferidos à mão (`tests/estatisticas_conhecidas.py`); e 297
  concursos aleatórios com semente fixa, comparando frequência, atrasos, pares, trios,
  distribuição e obrigatórias/excluídas com um cálculo direto em Python. Também: banco vazio,
  filtros inválidos (422) e todos os endpoints.
- Fase 3 no ambiente do usuário (Windows, Python 3.14.8, PostgreSQL 18.6), 2026-10-12:
  **111 passed**.
- Tela (frontend), 2026-10-12, no ambiente do assistente (Node 22.22): `npm run test` com
  **21 testes aprovados** (formatação; cliente da API, incluindo erro 422, erro 502 e backend
  desligado; volante; página de concursos com botão Atualizar, "ainda faltam", Caixa fora do
  ar, banco vazio; página de estatísticas com volante e troca para trios; troca de abas e
  aviso sempre visível). `npm run build` sem erros de tipo. A tela também foi aberta num
  navegador (Chromium) contra o backend real com 3.801 concursos sintéticos e uma Caixa
  simulada: o botão Atualizar inseriu o concurso 3802, todas as abas carregaram e o console
  do navegador não registrou erros.
- Tela no ambiente do usuário (Windows, Node 24.21.0), 2026-10-12: `npm run test` com
  **21 passed** e a tela aberta com os concursos reais.
- Fase 4 (estratégias, geração e conferência), 2026-10-12, no ambiente do assistente:
  backend **134 testes aprovados** (23 novos) e frontend **27 testes aprovados** (6 novos).
  Cobrem: catálogo carregado pela migração `0003` (inclusive `downgrade`/`upgrade`); validação
  de faixas; criar, editar, desativar e excluir estratégia (usada só desativa, 409); geração
  respeitando obrigatórias, excluídas e todas as faixas, sem jogos repetidos; mesma semente
  gera os mesmos jogos; cópia dos parâmetros não muda quando a estratégia é editada; regra
  "repetidas do concurso base"; regras impossíveis não gravam nada (422); conferência contra
  um concurso grava `avaliacoes` sem duplicar; conferência contra o histórico com valores
  conferidos à mão; todos os endpoints; e a aba Jogos com API simulada. A aba também foi usada
  num navegador contra o backend real (3.802 concursos sintéticos): criar estratégia, gerar
  5 jogos, conferir contra o concurso 3801 e ver o histórico de um jogo, sem erros no console.

Validação anterior, da especificação, num PostgreSQL 16 descartável fora do repositório:

Validação feita durante a revisão da especificação (2026-10-12), executada num PostgreSQL 16
descartável, fora do repositório:
- o esquema de referência de `BANCO_DE_DADOS.md` foi criado sem erros;
- as restrições recusaram: número duplicado, 14 dezenas, dezena repetida, 0, 26, `NULL`,
  ordem errada, array de duas dimensões, jogo com 21 dezenas, obrigatórias sobrepostas às
  excluídas, chave estrangeira inexistente e exclusão de concurso referenciado;
- `ON CONFLICT (numero) DO NOTHING` não duplicou concurso existente;
- todas as consultas estatísticas da seção 6 rodaram sobre 3.500 concursos sintéticos.

Isso valida o desenho, mas não substitui a suíte T01–T09, que será escrita com o código.
