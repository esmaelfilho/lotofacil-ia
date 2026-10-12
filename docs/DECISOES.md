# Registro de decisões arquiteturais

Cada decisão segue o formato: contexto, decisão, justificativa, consequências e situação.
Decisões não são apagadas. Quando forem revistas, uma nova entrada substitui a anterior e
a antiga passa a ter a situação "Substituída por ADR-NNN".

---

## ADR-001 — PostgreSQL como banco de dados oficial desde a primeira versão

- **Data:** 2026-10-12
- **Situação:** Aceita
- **Substitui:** a previsão anterior de usar SQLite como banco inicial do projeto.

### Contexto

O Sistema de Loteria Lotofácil armazena o histórico completo de concursos, as regras
estatísticas, as estratégias, as gerações de jogos, os jogos gerados, as avaliações e o
histórico de importações. Os cálculos estatísticos (frequências por janela, atrasos, pares
e trios, repetição entre concursos) são consultas de agregação sobre todo o histórico.

A ideia inicial era começar com SQLite e migrar depois. Essa migração tardia obrigaria a
reescrever migrações, revalidar restrições e reexecutar testes num banco com comportamento
diferente (tipagem, concorrência, funções de janela, arrays, `ON CONFLICT`, restrições).

### Decisão

1. PostgreSQL é o único banco oficial, em todos os ambientes: desenvolvimento, testes de
   integração e produção.
2. SQLite não é mantido como alternativa de produção nem como banco padrão de
   desenvolvimento.
3. Pilha de acesso a dados: SQLAlchemy 2.x (ORM, estilo 2.0), Psycopg 3 como driver
   (`postgresql+psycopg://`) e Alembic para todas as alterações estruturais.
4. O esquema é criado e alterado somente por migrações Alembic versionadas. A aplicação não
   chama `metadata.create_all()` em produção nem em desenvolvimento.
5. A conexão é configurada por variáveis de ambiente (`DATABASE_URL`, `TEST_DATABASE_URL`),
   validada na inicialização, e credenciais nunca aparecem em logs.
6. Os testes de integração do backend rodam num PostgreSQL real, num banco separado cujo
   nome termina em `_test`.

### Justificativa

- **Integridade no banco:** `CHECK` com função imutável, arrays `smallint[]`, chaves
  estrangeiras com ações definidas e restrições de unicidade garantem as regras da
  Lotofácil (15 dezenas distintas entre 1 e 25) mesmo se outro processo gravar dados.
- **Estatísticas em SQL:** funções de janela (`row_number`, `lag`), `unnest`, `FILTER` e
  agregações permitem calcular frequência, atraso, pares e trios direto no banco, sem
  tabelas redundantes.
- **Importação idempotente:** `INSERT ... ON CONFLICT (numero) DO NOTHING` torna a
  reimportação segura.
- **Paridade entre ambientes:** o que passa nos testes é o mesmo motor usado em produção.
- **Sem migração futura:** evita o custo e o risco de trocar de banco depois que já
  existirem dados reais.

### Consequências

- **Positivas:** regras de integridade aplicadas pelo banco; consultas estatísticas
  eficientes; testes que refletem o comportamento real; caminho de produção definido.
- **Negativas:** desenvolver e testar exige um servidor PostgreSQL (local, em contêiner ou
  remoto). O ambiente fica um pouco mais pesado que com SQLite.
- **Testes:** testes unitários puros (validação Pydantic, funções estatísticas em memória)
  não precisam de banco. Testes de integração precisam de `TEST_DATABASE_URL` e são
  ignorados com aviso explícito, nunca dados como aprovados, quando o banco não está
  disponível.
- **Migrações:** o autogenerate do Alembic não detecta funções SQL nem alguns `CHECK`;
  essas partes são escritas manualmente com `op.execute()` e revisadas a cada migração.
- **Instruções antigas:** qualquer instrução que mencione arquivo `.db`/`.sqlite`,
  `sqlite:///`, `check_same_thread` ou criação automática de tabelas está obsoleta.

---

## ADR-002 — Dezenas armazenadas como `smallint[]` ordenado

- **Data:** 2026-10-12
- **Situação:** Aceita

### Contexto

Cada resultado tem exatamente 15 dezenas distintas entre 1 e 25. O resultado não pode ser
reconstruído dependendo da ordem em que o banco devolve linhas.

### Decisão

As dezenas de um concurso ficam numa única coluna `dezenas smallint[]`, **sempre em ordem
crescente**. A restrição `ck_concursos_dezenas` usa a função imutável
`lotofacil_dezenas_validas(dezenas, 15, 15)`, que exige: uma dimensão, nenhum `NULL`,
valores entre 1 e 25, sem repetição, ordem estritamente crescente e a quantidade exata.
A mesma função valida jogos gerados (15 a 20 dezenas) e as listas de dezenas obrigatórias e
excluídas.

### Justificativa

- O resultado é lido e gravado como um valor só; a ordem faz parte do dado.
- Toda a regra cabe num `CHECK`, sem triggers.
- `unnest()` transforma o array em linhas quando a estatística precisa agrupar por dezena,
  com desempenho adequado (veja `docs/BANCO_DE_DADOS.md`).

### Alternativas consideradas

- **Tabela `concurso_dezenas` (uma linha por dezena):** boa para `GROUP BY`, mas exigiria
  trigger de restrição adiada para garantir exatamente 15 linhas e montaria o resultado
  com agregação.
- **Máscara de bits (inteiro de 25 bits):** compacta e rápida, porém ilegível e mais
  propensa a erro.

### Consequências

- O backend normaliza (ordena) as dezenas antes de gravar; o banco rejeita qualquer valor
  fora do padrão.
- A ordem em que as bolas foram sorteadas não é guardada nesta versão (veja pendências em
  `docs/BACKLOG.md`).

---

## ADR-003 — Estatísticas calculadas sob demanda, sem tabelas de pré-cálculo

- **Data:** 2026-10-12
- **Situação:** Aceita

### Decisão

As estatísticas são calculadas a partir de `concursos` por serviços do backend, usando
consultas SQL agregadas. Não há tabelas de frequência, atraso, pares ou trios.

### Justificativa

Numa validação com 3.500 concursos sintéticos em PostgreSQL 16, as consultas levaram de
menos de 1 ms (perfil de um concurso) a cerca de 240 ms (pares) e 840 ms (trios) sobre o
histórico inteiro. O volume real cresce cerca de 300 concursos por ano.

### Consequências

Se trios ou outra estatística ficarem lentos em produção, a solução prevista é uma
*materialized view* atualizada (`REFRESH MATERIALIZED VIEW CONCURRENTLY`) ao final de cada
importação concluída, registrada numa nova ADR com a medição que a justificou.
