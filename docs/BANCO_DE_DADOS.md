# Banco de dados

O banco oficial é o **PostgreSQL** (versão mínima 15, recomendada 16), em todos os
ambientes. A decisão está registrada em [`DECISOES.md`](DECISOES.md) (ADR-001).

- ORM: SQLAlchemy 2.x (estilo 2.0, tipos `Mapped[...]`).
- Driver: Psycopg 3 (`postgresql+psycopg://`).
- Migrações: Alembic. **Toda** alteração estrutural é uma migração versionada.
- Fuso: colunas de data e hora usam `timestamptz`; datas de sorteio usam `date`.

## 1. Bancos e usuários

| Banco | Uso | Quem acessa |
|---|---|---|
| `lotofacil` | desenvolvimento | aplicação local (`DATABASE_URL`) |
| `lotofacil_test` | testes de integração, recriado pelos testes | pytest (`TEST_DATABASE_URL`) |
| (produção) | definido no ambiente de implantação | aplicação (`DATABASE_URL`) |

O usuário da aplicação (`lotofacil_app` nos exemplos) é dono dos bancos de
desenvolvimento e teste, mas não é superusuário. Exemplo de criação local, executado como
administrador do PostgreSQL (`psql -U postgres`); a senha é digitada no momento e não fica
em arquivo versionado:

```sql
CREATE ROLE lotofacil_app LOGIN PASSWORD :'senha';   -- psql -v senha=...
CREATE DATABASE lotofacil      OWNER lotofacil_app ENCODING 'UTF8' TEMPLATE template0;
CREATE DATABASE lotofacil_test OWNER lotofacil_app ENCODING 'UTF8' TEMPLATE template0;
```

Opção com contêiner (o `docker-compose.yml` ainda não existe; está no backlog):

```bash
docker run --name lotofacil-pg -e POSTGRES_USER=lotofacil_app \
  -e POSTGRES_PASSWORD=<escolha-uma-senha> -e POSTGRES_DB=lotofacil \
  -p 5432:5432 -d postgres:16
docker exec -it lotofacil-pg createdb -U lotofacil_app lotofacil_test
```

## 2. Representação das dezenas

As dezenas são guardadas numa coluna `smallint[]` **em ordem crescente** (ADR-002). A
função `lotofacil_dezenas_validas(d, qtd_min, qtd_max)` é `IMMUTABLE` e é usada nos `CHECK`:

- array de uma dimensão, sem `NULL`;
- todos os valores entre 1 e 25;
- sem repetição e em ordem estritamente crescente;
- quantidade entre `qtd_min` e `qtd_max`.

| Coluna | Quantidade aceita |
|---|---|
| `concursos.dezenas` | exatamente 15 |
| `jogos_gerados.dezenas` | 15 a 20 (apostas oficiais da Lotofácil) |
| `geracoes_jogos.dezenas_obrigatorias` | 0 a 20 |
| `geracoes_jogos.dezenas_excluidas` | 0 a 10 (sobram ao menos 15 dezenas) |

O backend valida as mesmas regras com Pydantic **antes** de gravar e devolve mensagens
claras. A restrição do banco é a última barreira. As dezenas são ordenadas pelo backend;
o banco recusa arrays fora de ordem em vez de reordená-los silenciosamente.

Na API e na interface as dezenas são exibidas com dois dígitos (`01` a `25`); no banco são
números.

## 3. Tabelas

| Tabela | Finalidade |
|---|---|
| `concursos` | resultados oficiais; `numero` único, `data_sorteio`, `dezenas` |
| `historico_importacoes` | cada execução de importação, com contagens e situação |
| `regras_estatisticas` | catálogo de regras usadas como filtros (pares/ímpares, soma, primos...) |
| `estrategias` | conjuntos nomeados de regras |
| `estrategia_regras` | associação estratégia × regra, com os parâmetros escolhidos |
| `geracoes_jogos` | cada pedido de geração: estratégia, concurso base, parâmetros, dezenas obrigatórias e excluídas |
| `jogos_gerados` | jogos produzidos por uma geração |
| `avaliacoes` | conferência de um jogo gerado contra um concurso (acertos) |

`estrategia_regras` não estava na lista original de tabelas. Ela existe porque uma
estratégia usa várias regras e cada regra pode estar em várias estratégias; sem ela a
relação ficaria num JSON sem chave estrangeira.

### Regras de integridade

- `concursos.numero` é único (`uq_concursos_numero`) e positivo.
- Excluir um concurso usado como base de uma geração ou numa avaliação é bloqueado
  (`ON DELETE RESTRICT`).
- Excluir uma geração exclui seus jogos e, em cascata, as avaliações desses jogos.
- Uma regra usada por alguma estratégia não pode ser excluída; deve ser desativada
  (`ativa = false`).
- Uma estratégia usada por alguma geração não pode ser excluída; deve ser desativada.
- `geracoes_jogos.parametros` guarda uma **cópia** das regras e parâmetros usados no
  momento da geração. Assim, alterar a estratégia depois não muda o significado das
  gerações antigas. `semente` permite reproduzir a geração.
- Dezenas obrigatórias e excluídas não podem se sobrepor, as obrigatórias cabem no jogo e
  as excluídas deixam dezenas suficientes.
- Um jogo não se repete dentro da mesma geração (`uq_jogos_geracao_dezenas`).
- Cada jogo é avaliado no máximo uma vez por concurso (`uq_avaliacoes_jogo_concurso`).
- `avaliacoes.acertos` é derivado de `jogos_gerados.dezenas` e `concursos.dezenas`, que não
  mudam depois de gravados. Fica armazenado porque é o registro da conferência que o
  usuário pediu; o serviço sempre o calcula, nunca recebe da interface.

### Índices e justificativa

| Índice | Justificativa |
|---|---|
| `uq_concursos_numero` (único) | busca por número, ordenação dos "últimos N concursos", `ON CONFLICT` da importação, chave referenciada por `geracoes_jogos` |
| `ix_concursos_data_sorteio` | filtro e listagem por período |
| `ix_concursos_importacao_id` | rastrear o que uma importação inseriu |
| `ix_estrategia_regras_regra_id` | verificar uso de uma regra antes de desativar/excluir (a PK já cobre a busca por estratégia) |
| `ix_geracoes_jogos_estrategia_id`, `ix_geracoes_jogos_concurso_base` | chaves estrangeiras; listar gerações por estratégia/concurso e checar `RESTRICT` |
| `uq_jogos_geracao_sequencia` | lista os jogos de uma geração em ordem (cobre a FK `geracao_id`) |
| `ix_avaliacoes_concurso_id` | avaliações de um concurso e checagem de `RESTRICT` (a única `jogo_id, concurso_id` cobre a busca por jogo) |

**Não criados, de propósito:** índice GIN em `dezenas` (as estatísticas percorrem o histórico
inteiro; não há busca seletiva por dezena que o justifique) e índices em colunas JSONB.
Novos índices exigem uma consulta real com `EXPLAIN ANALYZE` que mostre o ganho.

## 4. Esquema de referência

A migração inicial do Alembic deve produzir exatamente este esquema. A função é criada com
`op.execute()` antes das tabelas, e o `downgrade` remove tabelas e depois a função. Este
SQL foi executado com sucesso num PostgreSQL 16. Nele, chaves primárias e estrangeiras
usam os nomes padrão do PostgreSQL; na migração elas seguem a convenção da seção 8.

```sql
-- Função de validação das dezenas (IMMUTABLE para poder ser usada em CHECK).
-- Válido quando: sem NULL, todos entre 1 e 25, sem repetição, em ordem
-- estritamente crescente e com quantidade entre qtd_min e qtd_max.
CREATE FUNCTION lotofacil_dezenas_validas(d smallint[], qtd_min int, qtd_max int)
RETURNS boolean
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
AS $$
    SELECT array_ndims(d) = 1
       AND cardinality(d) BETWEEN qtd_min AND qtd_max
       AND d = ARRAY(SELECT DISTINCT x FROM unnest(d) AS x
                     WHERE x BETWEEN 1 AND 25 ORDER BY x)
$$;

CREATE TABLE historico_importacoes (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origem          varchar(20)  NOT NULL CHECK (origem IN ('ARQUIVO', 'API')),
    referencia      varchar(255) NOT NULL,
    hash_conteudo   char(64),
    status          varchar(20)  NOT NULL DEFAULT 'EM_ANDAMENTO'
                    CHECK (status IN ('EM_ANDAMENTO', 'CONCLUIDA', 'CONCLUIDA_COM_REJEICOES', 'FALHOU')),
    total_lidos     integer NOT NULL DEFAULT 0 CHECK (total_lidos >= 0),
    total_inseridos integer NOT NULL DEFAULT 0 CHECK (total_inseridos >= 0),
    total_ignorados integer NOT NULL DEFAULT 0 CHECK (total_ignorados >= 0),
    total_rejeitados integer NOT NULL DEFAULT 0 CHECK (total_rejeitados >= 0),
    mensagem_erro   text,
    iniciada_em     timestamptz NOT NULL DEFAULT now(),
    finalizada_em   timestamptz,
    CHECK (finalizada_em IS NULL OR finalizada_em >= iniciada_em)
);

CREATE TABLE concursos (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero          integer  NOT NULL CHECK (numero > 0),
    data_sorteio    date     NOT NULL,
    dezenas         smallint[] NOT NULL
                    CONSTRAINT ck_concursos_dezenas CHECK (lotofacil_dezenas_validas(dezenas, 15, 15)),
    importacao_id   bigint REFERENCES historico_importacoes (id) ON DELETE SET NULL,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_concursos_numero UNIQUE (numero)
);
CREATE INDEX ix_concursos_data_sorteio ON concursos (data_sorteio);
CREATE INDEX ix_concursos_importacao_id ON concursos (importacao_id);

CREATE TABLE regras_estatisticas (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo      varchar(50)  NOT NULL CONSTRAINT uq_regras_codigo UNIQUE,
    nome        varchar(120) NOT NULL,
    descricao   text,
    parametros_padrao jsonb NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(parametros_padrao) = 'object'),
    ativa       boolean NOT NULL DEFAULT true
);

CREATE TABLE estrategias (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome          varchar(120) NOT NULL CONSTRAINT uq_estrategias_nome UNIQUE,
    descricao     text,
    ativa         boolean NOT NULL DEFAULT true,
    criada_em     timestamptz NOT NULL DEFAULT now(),
    atualizada_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE estrategia_regras (
    estrategia_id bigint NOT NULL REFERENCES estrategias (id) ON DELETE CASCADE,
    regra_id      bigint NOT NULL REFERENCES regras_estatisticas (id) ON DELETE RESTRICT,
    parametros    jsonb  NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(parametros) = 'object'),
    PRIMARY KEY (estrategia_id, regra_id)
);
CREATE INDEX ix_estrategia_regras_regra_id ON estrategia_regras (regra_id);

CREATE TABLE geracoes_jogos (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    estrategia_id        bigint REFERENCES estrategias (id) ON DELETE RESTRICT,
    concurso_base_numero integer NOT NULL REFERENCES concursos (numero) ON DELETE RESTRICT,
    quantidade_jogos     integer  NOT NULL CHECK (quantidade_jogos > 0),
    dezenas_por_jogo     smallint NOT NULL DEFAULT 15 CHECK (dezenas_por_jogo BETWEEN 15 AND 20),
    dezenas_obrigatorias smallint[] NOT NULL DEFAULT '{}'
                         CHECK (lotofacil_dezenas_validas(dezenas_obrigatorias, 0, 20)),
    dezenas_excluidas    smallint[] NOT NULL DEFAULT '{}'
                         CHECK (lotofacil_dezenas_validas(dezenas_excluidas, 0, 10)),
    parametros           jsonb NOT NULL CHECK (jsonb_typeof(parametros) = 'object'),
    semente              bigint,
    criada_em            timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_geracoes_obrigatorias_excluidas_disjuntas
        CHECK (NOT (dezenas_obrigatorias && dezenas_excluidas)),
    CONSTRAINT ck_geracoes_obrigatorias_cabem
        CHECK (cardinality(dezenas_obrigatorias) <= dezenas_por_jogo),
    CONSTRAINT ck_geracoes_excluidas_permitem_jogo
        CHECK (25 - cardinality(dezenas_excluidas) >= dezenas_por_jogo)
);
CREATE INDEX ix_geracoes_jogos_estrategia_id ON geracoes_jogos (estrategia_id);
CREATE INDEX ix_geracoes_jogos_concurso_base ON geracoes_jogos (concurso_base_numero);

CREATE TABLE jogos_gerados (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geracao_id bigint  NOT NULL REFERENCES geracoes_jogos (id) ON DELETE CASCADE,
    sequencia  integer NOT NULL CHECK (sequencia > 0),
    dezenas    smallint[] NOT NULL
               CONSTRAINT ck_jogos_dezenas CHECK (lotofacil_dezenas_validas(dezenas, 15, 20)),
    CONSTRAINT uq_jogos_geracao_sequencia UNIQUE (geracao_id, sequencia),
    CONSTRAINT uq_jogos_geracao_dezenas UNIQUE (geracao_id, dezenas)
);

CREATE TABLE avaliacoes (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    jogo_id     bigint   NOT NULL REFERENCES jogos_gerados (id) ON DELETE CASCADE,
    concurso_id bigint   NOT NULL REFERENCES concursos (id) ON DELETE RESTRICT,
    acertos     smallint NOT NULL CHECK (acertos BETWEEN 0 AND 15),
    avaliada_em timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_avaliacoes_jogo_concurso UNIQUE (jogo_id, concurso_id)
);
CREATE INDEX ix_avaliacoes_concurso_id ON avaliacoes (concurso_id);
```

## 5. Importação idempotente

1. Cria um registro em `historico_importacoes` com `status = 'EM_ANDAMENTO'` e o
   `hash_conteudo` (SHA-256) do arquivo ou resposta, numa transação própria.
2. Valida cada linha com Pydantic. Linhas inválidas são contadas em `total_rejeitados`, com
   o motivo no log da importação, e não interrompem as válidas.
3. Insere em lotes, numa transação, com
   `INSERT ... ON CONFLICT (numero) DO NOTHING RETURNING numero`.
   Os não retornados contam como `total_ignorados`.
4. Concurso já existente com dezenas ou data **diferentes** não é sobrescrito: é contado como
   rejeitado e informado como divergência.
5. Ao final, atualiza o registro para `CONCLUIDA`, `CONCLUIDA_COM_REJEICOES` ou `FALHOU`.
   Em falha, a transação dos dados é desfeita (`ROLLBACK`), mas o registro da importação
   permanece com a mensagem de erro.

Importar o mesmo arquivo duas vezes não altera os concursos: a segunda execução termina com
`total_inseridos = 0`.

## 6. Consultas estatísticas

Os serviços em `backend/app/services/estatisticas/` usam consultas como as abaixo, todas
executadas com sucesso sobre 3.500 concursos sintéticos em PostgreSQL 16 (tempos medidos no
ambiente de validação, apenas como ordem de grandeza).

Definições do volante 5×5: linha = `(d-1)/5+1`, coluna = `(d-1)%5+1`; miolo =
`{7,8,9,12,13,14,17,18,19}` (9 dezenas), moldura = as outras 16; primos =
`{2,3,5,7,11,13,17,19,23}`; Fibonacci = `{1,2,3,5,8,13,21}`; múltiplos de 3 =
`{3,6,9,12,15,18,21,24}`.

As janelas ("últimos N concursos") são definidas pela ordem de `numero`, nunca pela ordem
física de retorno. O atraso usa posição sequencial (`row_number`), para não depender de a
numeração não ter lacunas.

**Frequência total e nas janelas de 10, 50 e 100** (~16 ms):

```sql
WITH ordenados AS (
  SELECT dezenas, row_number() OVER (ORDER BY numero DESC) AS pos FROM concursos
)
SELECT d AS dezena, count(*) AS total,
       count(*) FILTER (WHERE pos <= 10)  AS janela_10,
       count(*) FILTER (WHERE pos <= 50)  AS janela_50,
       count(*) FILTER (WHERE pos <= 100) AS janela_100
FROM ordenados, unnest(dezenas) AS d
GROUP BY d ORDER BY d;
```

**Atraso atual e maior atraso histórico** (~34 ms):

```sql
WITH c AS (SELECT dezenas, row_number() OVER (ORDER BY numero) AS seq FROM concursos),
tot AS (SELECT max(seq) AS m FROM c),
ap AS (
  SELECT d, seq,
         seq - coalesce(lag(seq) OVER (PARTITION BY d ORDER BY seq), 0) - 1 AS intervalo
  FROM c, unnest(dezenas) AS d
)
SELECT d AS dezena,
       (SELECT m FROM tot) - max(seq) AS atraso_atual,
       greatest(max(intervalo), (SELECT m FROM tot) - max(seq)) AS maior_atraso
FROM ap GROUP BY d ORDER BY d;
```

Uma dezena que nunca saiu não aparece no resultado; o serviço completa as 25 dezenas
(atraso = total de concursos).

**Perfil de cada concurso** (pares, primos, soma, miolo, Fibonacci, múltiplos de 3), < 1 ms
por concurso:

```sql
SELECT numero,
  (SELECT count(*) FROM unnest(dezenas) x WHERE x % 2 = 0)                         AS pares,
  (SELECT count(*) FROM unnest(dezenas) x WHERE x = ANY('{2,3,5,7,11,13,17,19,23}')) AS primos,
  (SELECT sum(x)   FROM unnest(dezenas) x)                                           AS soma,
  (SELECT count(*) FROM unnest(dezenas) x WHERE x = ANY('{7,8,9,12,13,14,17,18,19}')) AS miolo,
  (SELECT count(*) FROM unnest(dezenas) x WHERE x = ANY('{1,2,3,5,8,13,21}'))         AS fibonacci,
  (SELECT count(*) FROM unnest(dezenas) x WHERE x % 3 = 0)                          AS multiplos_3
FROM concursos ORDER BY numero DESC;
```

Ímpares = 15 − pares; moldura = 15 − miolo.

**Distribuição por linha** (por coluna, troque `(x-1)/5+1` por `(x-1)%5+1`):

```sql
SELECT numero, array_agg(qtd ORDER BY linha) AS por_linha
FROM (SELECT numero, (x - 1) / 5 + 1 AS linha, count(*) AS qtd
      FROM concursos, unnest(dezenas) x GROUP BY 1, 2) t
GROUP BY numero;
```

Uma linha sem dezenas não aparece no `array_agg`; o serviço completa com zero.

**Sequências consecutivas** (técnica *gaps and islands*):

```sql
SELECT numero, max(tam) AS maior_sequencia, count(*) FILTER (WHERE tam >= 2) AS blocos
FROM (SELECT numero, count(*) AS tam
      FROM (SELECT numero, x, x - row_number() OVER (PARTITION BY numero ORDER BY x) AS g
            FROM concursos, unnest(dezenas) x) s
      GROUP BY numero, g) t
GROUP BY numero;
```

**Repetição em relação ao concurso anterior** (~3 ms):

```sql
SELECT numero, (SELECT count(*) FROM unnest(dezenas) x WHERE x = ANY(anterior)) AS repetidas
FROM (SELECT numero, dezenas, lag(dezenas) OVER (ORDER BY numero) AS anterior FROM concursos) t
WHERE anterior IS NOT NULL;
```

**Pares mais frequentes** (~240 ms) e **trios mais frequentes** (~840 ms):

```sql
SELECT a.x AS d1, b.x AS d2, count(*) AS vezes
FROM concursos c, unnest(c.dezenas) a(x), unnest(c.dezenas) b(x)
WHERE a.x < b.x GROUP BY 1, 2 ORDER BY vezes DESC LIMIT :limite;

SELECT a.x AS d1, b.x AS d2, t.x AS d3, count(*) AS vezes
FROM concursos c, unnest(c.dezenas) a(x), unnest(c.dezenas) b(x), unnest(c.dezenas) t(x)
WHERE a.x < b.x AND b.x < t.x GROUP BY 1, 2, 3 ORDER BY vezes DESC LIMIT :limite;
```

**Conferência de um jogo contra todo o histórico** (~43 ms):

```sql
SELECT acertos, count(*) FROM (
  SELECT cardinality(ARRAY(SELECT unnest(dezenas) INTERSECT SELECT unnest(:jogo::smallint[]))) AS acertos
  FROM concursos) t
WHERE acertos >= 11 GROUP BY acertos ORDER BY acertos;
```

**Quentes e frias**: ranking da frequência numa janela (padrão: últimos 50 concursos), as 5
mais frequentes são quentes e as 5 menos frequentes são frias. Janela e quantidade são
parâmetros da consulta.

**Dezenas obrigatórias e excluídas**: são filtros da geração, gravados em `geracoes_jogos`.
A estatística correspondente mostra, para um conjunto informado, em quantos concursos
históricos todas as obrigatórias saíram e nenhuma excluída saiu (`dezenas @> :obrigatorias
AND NOT dezenas && :excluidas`).

## 7. Cache e pré-cálculo

Nenhum, nesta versão (ADR-003). Se for necessário, a opção prevista é uma *materialized
view* por estatística lenta, criada por migração e atualizada ao final de cada importação
concluída com novos concursos. A justificativa e a medição serão registradas em
`DECISOES.md` antes da criação.

## 8. Regras para migrações

- Uma migração por mudança lógica, com `upgrade` e `downgrade` testados.
- Gerar com `alembic revision --autogenerate -m "..."` e **revisar sempre**: o autogenerate
  não detecta funções SQL e pode omitir `CHECK`. Use `op.execute()` para essas partes.
- Nomes de restrições seguem a convenção do `MetaData(naming_convention=...)`:
  `pk_%(table_name)s`, `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`,
  `uq_%(table_name)s_%(column_0_name)s`, `ck_%(table_name)s_%(constraint_name)s`,
  `ix_%(column_0_label)s`.
- Migrações de dados (por exemplo, carga inicial de `regras_estatisticas`) ficam em
  migrações separadas das estruturais.
- Nunca editar uma migração já aplicada em outro ambiente; criar uma nova.
