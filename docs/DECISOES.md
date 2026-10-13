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

---

## ADR-004 — Concursos atualizados pela API de resultados da Caixa

- **Data:** 2026-10-12
- **Situação:** Aceita

### Contexto

O usuário quer um botão que atualize os concursos a partir do último cadastrado, sem baixar
planilhas manualmente.

### Decisão

- Fonte: `https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil` (último concurso) e
  `.../lotofacil/{numero}` (concurso específico), configuráveis por `CAIXA_API_URL`.
- São buscados apenas os números que faltam no banco, de 1 até o último sorteado.
- Cliente HTTP da biblioteca padrão (`urllib`), usando os certificados e o proxy do sistema;
  pausa entre pedidos (`CAIXA_PAUSA_SEGUNDOS`, padrão 0,3 s) e até 3 tentativas.
- Gravação em lotes de 50 com `ON CONFLICT DO NOTHING`; cada lote é uma transação.
- Primeira carga pelo comando `python -m app.comandos.atualizar_concursos`, que mostra o
  progresso; atualizações seguintes pelo endpoint `POST /concursos/atualizar` (padrão de 300
  concursos por chamada).

### Justificativa

Atualização em um passo, sem arquivos manuais. Lotes independentes evitam perder minutos de
download se a conexão cair perto do fim; como cada concurso gravado é completo e validado
(pelo backend e pelo `CHECK` do banco), mantê-los não compromete a integridade.

### Consequências

- A API **não é documentada oficialmente**: pode mudar de formato, ficar fora do ar ou
  bloquear acessos. O sistema valida tudo o que recebe, informa o problema com clareza e não
  altera concursos já gravados. Uma importação por arquivo continua prevista como alternativa.
- Diferença em relação à ideia original de "desfazer tudo em caso de falha": na fonte API, só
  o lote com erro é desfeito (RF-02.5 atualizado).
- Os testes nunca acessam a internet: usam uma Caixa simulada com o formato real da resposta
  (`backend/tests/dados/caixa_lotofacil_3802.json`).

---

## ADR-005 — Perfil dos concursos calculado em Python; agregações em SQL

- **Data:** 2026-10-12
- **Situação:** Aceita
- **Complementa:** ADR-003.

### Contexto

O perfil de um concurso (pares, primos, soma, moldura/miolo, linhas, colunas, sequências,
Fibonacci, múltiplos de 3, repetidas do anterior) será usado também para filtrar os jogos
gerados na Fase 4. Ter a mesma regra escrita em SQL e em Python abriria espaço para as duas
divergirem.

### Decisão

- Frequência, janelas, atraso, obrigatórias/excluídas, pares e trios são calculados pelo
  PostgreSQL (consultas da seção 6 de `BANCO_DE_DADOS.md`).
- O perfil é calculado por funções Python puras (`app/services/estatisticas/perfil.py`) sobre
  as dezenas lidas do banco. A distribuição de uma característica lê as dezenas de todos os
  concursos (ou dos últimos N) e conta em Python.

### Justificativa

Uma só definição de cada característica, testável sem banco. Medição com 3.802 concursos
sintéticos (PostgreSQL 16, ambiente do assistente): distribuição ~70 ms; perfil de 20
concursos ~2 ms; frequência ~18 ms; atrasos ~68 ms; pares ~190 ms; trios ~730 ms.

### Consequências

Nenhuma tabela nova. Se o volume crescer a ponto de a distribuição ficar lenta, a alternativa
é calcular em SQL com testes que comparem os dois resultados.

---

## ADR-006 — A tela fala com a API pelo proxy do Vite

- **Data:** 2026-10-12
- **Situação:** Aceita

### Contexto

Em desenvolvimento a tela roda em `http://localhost:5173` (Vite) e a API em
`http://localhost:8000` (uvicorn). Por segurança, o navegador bloqueia chamadas entre
endereços diferentes, a menos que o servidor libere (CORS).

### Decisão

A tela chama sempre `/api/...` no próprio endereço. O servidor do Vite repassa essas chamadas
para `VITE_API_URL` (padrão `http://localhost:8000`), removendo o prefixo `/api`. O
`vite.config.ts` lê o `.env` da raiz, carregando apenas variáveis que começam com `VITE_`.

### Justificativa

O backend não precisa de nenhuma alteração nem de configuração de CORS; o navegador vê um
endereço só. Uso local por um único usuário, sem login (fora do escopo).

### Consequências

Para publicar a tela fora do ambiente de desenvolvimento, será preciso servir os arquivos de
`frontend/dist` atrás do mesmo endereço da API (ou liberar CORS), o que fica para uma nova ADR.

---

## ADR-007 — Geração de jogos por sorteio com filtro e semente registrada

- **Data:** 2026-10-12
- **Situação:** Aceita

### Contexto

A geração precisa respeitar dezenas obrigatórias, excluídas e as faixas de uma estratégia
(RF-05.1), não repetir jogos (RF-05.2) e ser reproduzível mesmo que a estratégia mude depois
(RF-05.3).

### Decisão

- As regras são faixas (mínimo e máximo inclusivos) sobre valores do jogo calculados por
  `estatisticas/perfil.py` (mesma definição das estatísticas, ADR-005).
- O serviço sorteia combinações com `random.Random(semente)`: obrigatórias + dezenas
  sorteadas entre as livres. Mantém as que passam em todas as faixas e ainda não saíram,
  até a quantidade pedida ou 100.000 tentativas.
- A `semente` é informada pelo usuário ou sorteada (`SystemRandom`, até 2^53, para caber no
  JavaScript) e gravada em `geracoes_jogos.semente`. A cópia das regras usadas vai em
  `geracoes_jogos.parametros`.
- Se as faixas não permitirem a quantidade pedida, nada é gravado e a resposta informa quantos
  jogos foram encontrados.
- Faixas valem para o jogo inteiro: em jogos de 16 a 20 dezenas o usuário ajusta as faixas.

### Justificativa

Simples, sem viés entre os jogos válidos (cada combinação válida tem a mesma chance de ser
escolhida) e fácil de testar. Com as faixas padrão a taxa de aceitação é alta; 100 jogos levam
milissegundos. O limite de tentativas impede travar com regras impossíveis (cerca de 2 s no
pior caso, medido no ambiente do assistente).

### Consequências

- A reprodução exata depende do algoritmo de `random.Random` do Python, estável entre versões
  do CPython para `sample()` com a mesma semente; a geração grava o nome do algoritmo em
  `parametros` para registro.
- Estratégias muito restritivas podem não gerar; a mensagem orienta afrouxar alguma faixa.

## ADR-008 — Teste de estratégia com base no concurso anterior e gravação opcional

- **Data:** 2026-10-13
- **Situação:** Aceita

### Contexto

O usuário quer testar uma estratégia num concurso que já saiu, para ver quantas dezenas os
jogos teriam acertado (RF-07), e escolher quais jogos gravar (RF-05.4). Até aqui, toda
geração era gravada.

### Decisão

- O teste gera os jogos de cada estratégia com **base no concurso anterior** ao testado
  (o maior número menor que ele, o que cobre lacunas na numeração). O resultado testado
  nunca entra na geração; assim a regra "repetidas do concurso base" usa o que se conhecia
  na véspera.
- O teste usa o mesmo `sortear_jogos` da geração e a mesma semente para todas as estratégias.
  Estratégias desativadas não podem ser testadas, como na geração.
- O teste só consulta: não grava geração nem avaliação. Uma estratégia que não encontra
  jogos suficientes aparece com aviso, sem interromper as outras.
- `POST /geracoes` ganhou `gravar` (padrão `true`, compatível com quem já usa a API). Com
  `false`, devolve os jogos sem `id`. Para gravar depois, a tela reenvia os mesmos
  parâmetros com a semente e o concurso base devolvidos; pela ADR-007, isso reproduz
  exatamente os mesmos jogos. Gravar a partir do teste também já confere os jogos com o
  concurso testado (grava `avaliacoes`).
- Nenhuma tabela nova: o teste é calculado na hora (ADR-003).

### Justificativa

Usar o concurso anterior como base evita que o teste "olhe o futuro". Reaproveitar a semente
para gravar evita guardar prévias no banco ou mandar os jogos de volta do navegador, e o
backend continua sendo quem gera e valida os jogos.

### Consequências

- Gravar depende de a geração ser reproduzível (ADR-007); os testes conferem que os jogos
  gravados são os mesmos mostrados.
- Um teste mostra um concurso por vez. Testar muitos concursos de uma vez (acúmulo ao longo
  do tempo) fica para outro passo, se for pedido.
