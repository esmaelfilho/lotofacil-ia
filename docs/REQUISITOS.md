# Requisitos

Sistema para análise estatística e geração de jogos da **Lotofácil** (25 dezenas, 15
sorteadas por concurso). Uso por um único usuário, sem login nesta versão.

> Aviso obrigatório na interface: cada sorteio é independente. As estatísticas descrevem
> resultados passados e não aumentam a chance de acerto.

## 1. Requisitos funcionais

### RF-01 Concursos
- RF-01.1 Cadastrar e consultar concursos: número, data do sorteio e 15 dezenas.
- RF-01.2 O número do concurso é único; tentar cadastrar um número existente é recusado
  com mensagem clara.
- RF-01.3 Cada resultado tem exatamente 15 dezenas distintas entre 01 e 25. A validação é
  feita no backend e reforçada por restrição no banco.
- RF-01.4 Listar concursos com filtro por número e por período, ordenados por número.

### RF-02 Importação
- RF-02.1 Atualizar os concursos pela API de resultados da Caixa, buscando somente os que
  faltam no banco (do concurso 1 até o último sorteado, incluindo lacunas). Disponível como
  endpoint `POST /concursos/atualizar` (o "botão Atualizar") e como comando de terminal para a
  primeira carga. Importação de arquivo (planilha ou CSV) fica como alternativa futura.
- RF-02.2 A importação é idempotente: reimportar o mesmo conteúdo não duplica nem altera
  concursos.
- RF-02.3 Concurso existente com dados divergentes não é sobrescrito; a divergência é
  reportada.
- RF-02.4 Cada importação fica registrada com origem, data, situação e totais de lidos,
  inseridos, ignorados e rejeitados.
- RF-02.5 Falha durante a importação registra o erro no histórico. Na importação pela API, os
  concursos são gravados em lotes: se a Caixa parar de responder no meio, os lotes já gravados
  (concursos completos e válidos) são mantidos e a próxima execução continua de onde parou
  (ADR-004). Um lote com erro é desfeito por inteiro.
- RF-02.6 Cada execução busca no máximo um número configurável de concursos (padrão 300 pelo
  endpoint), informando quantos ainda faltam.

### RF-03 Estatísticas
Todas calculadas a partir dos concursos históricos:
- RF-03.1 Frequência de cada dezena no total e nas janelas dos últimos 10, 50 e 100
  concursos.
- RF-03.2 Dezenas quentes e frias (por padrão, as 5 mais e as 5 menos frequentes na janela
  de 50 concursos; janela e quantidade configuráveis).
- RF-03.3 Atraso atual e maior atraso histórico de cada dezena.
- RF-03.4 Quantidade de pares e ímpares por concurso e sua distribuição.
- RF-03.5 Quantidade de primos por concurso (2, 3, 5, 7, 11, 13, 17, 19, 23).
- RF-03.6 Soma das dezenas por concurso e sua distribuição.
- RF-03.7 Moldura (16 dezenas da borda) e miolo (7, 8, 9, 12, 13, 14, 17, 18, 19).
- RF-03.8 Distribuição por linha e por coluna do volante 5×5.
- RF-03.9 Dezenas obrigatórias e excluídas: em quantos concursos todas as obrigatórias
  saíram e nenhuma excluída saiu.
- RF-03.10 Sequências de dezenas consecutivas (maior sequência e quantidade de blocos).
- RF-03.11 Números de Fibonacci (1, 2, 3, 5, 8, 13, 21) e múltiplos de 3 por concurso.
- RF-03.12 Repetição de dezenas em relação ao concurso anterior.
- RF-03.13 Pares e trios de dezenas que mais saíram juntos.

### RF-04 Regras e estratégias
- RF-04.1 Catálogo de regras estatísticas usáveis como filtro (ex.: pares entre 7 e 8, soma
  entre 180 e 220).
- RF-04.2 Criar, editar e desativar estratégias compostas por regras com parâmetros.
- RF-04.3 Regras e estratégias já usadas em gerações não são excluídas, apenas desativadas.

### RF-05 Geração de jogos
- RF-05.1 Gerar N jogos a partir de uma estratégia, de dezenas obrigatórias e de dezenas
  excluídas, tendo um concurso como base.
- RF-05.2 Jogos têm de 15 a 20 dezenas (padrão 15), sem repetição de jogo na mesma geração.
- RF-05.3 A geração guarda uma cópia dos parâmetros usados e a semente, para ser
  reproduzível mesmo que a estratégia mude depois.
- RF-05.4 Gravar é opcional: os jogos gerados podem ser só mostrados e gravados depois, com
  os mesmos jogos (mesma semente, mesma base e mesmos parâmetros).

### RF-06 Avaliação
- RF-06.1 Conferir jogos gerados contra um concurso e registrar os acertos.
- RF-06.2 Conferir um jogo contra todo o histórico e mostrar quantas vezes teria feito 11,
  12, 13, 14 e 15 pontos.

### RF-07 Testar estratégia
- RF-07.1 Escolher um concurso que já saiu e uma ou mais estratégias (e, para comparar, jogos
  sem estratégia) e ver quantas dezenas cada jogo gerado teria acertado.
- RF-07.2 Os jogos do teste são gerados como se fosse a véspera do concurso: a base é o
  concurso anterior, e o resultado testado não é usado para gerar.
- RF-07.3 O teste mostra, por estratégia, o maior acerto, a média de acertos e quantos jogos
  fizeram 11, 12, 13, 14 e 15 pontos. Nada é gravado, a não ser que o usuário peça para
  gravar os jogos de uma estratégia; nesse caso eles são gravados e já conferidos com o
  concurso testado.

## 2. Requisitos não funcionais

- RNF-01 **Banco de dados:** PostgreSQL é o banco oficial em todos os ambientes desde a
  primeira versão. SQLite não é usado (ADR-001).
- RNF-02 **Migrações:** o esquema é criado e alterado somente por migrações Alembic
  versionadas; a aplicação não cria tabelas automaticamente.
- RNF-03 **Configuração:** conexão por variáveis de ambiente (`DATABASE_URL`). Nenhuma senha
  real no código ou no repositório; `.env` fica fora do Git e `.env.example` traz valores
  demonstrativos.
- RNF-04 **Inicialização:** a aplicação valida a configuração e testa a conexão ao iniciar;
  se falhar, encerra com mensagem útil (host, porta, banco e causa provável), sem expor a
  senha.
- RNF-05 **Logs:** credenciais e URLs de conexão completas nunca são registradas.
- RNF-06 **Integridade:** chaves primárias e estrangeiras, unicidade e `CHECK` no banco,
  além da validação no backend.
- RNF-07 **Desempenho:** estatísticas calculadas no banco com consultas agregadas; sem
  tabelas redundantes. Qualquer cache ou pré-cálculo precisa de justificativa documentada.
- RNF-08 **Testes:** integração do backend em PostgreSQL real, num banco isolado; testes
  nunca alteram o banco de desenvolvimento.
- RNF-09 **Tecnologias:** Python com FastAPI, Pydantic, SQLAlchemy 2.x, Alembic e Psycopg 3;
  frontend com React, TypeScript, Vite, Material UI e Recharts; pytest e Vitest.

## 3. Fora do escopo desta versão

- Login, autenticação e múltiplos usuários.
- Outras loterias além da Lotofácil.
- Apostas online ou integração com a Caixa para apostar.
- Histórico de prêmios e acumulações (está no backlog).
