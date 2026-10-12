// Respostas de exemplo da API, no formato real.
export const CONCURSO_3802 = {
  id: 3802,
  numero: 3802,
  data_sorteio: '2026-10-10',
  dezenas: [1, 2, 4, 5, 7, 9, 10, 12, 14, 16, 18, 20, 22, 23, 25],
}

export const paginaConcursos = (total = 3802) => ({
  total,
  itens: total ? [CONCURSO_3802] : [],
})

export const IMPORTACAO = {
  id: 1,
  origem: 'API_CAIXA',
  referencia: 'servicebus2.caixa.gov.br',
  status: 'CONCLUIDA',
  total_lidos: 3802,
  total_inseridos: 3802,
  total_ignorados: 0,
  total_rejeitados: 0,
  mensagem_erro: null,
  iniciada_em: '2026-10-12T20:00:00+00:00',
  finalizada_em: '2026-10-12T20:25:00+00:00',
}

const DEZENAS = Array.from({ length: 25 }, (_, i) => i + 1)

export const FREQUENCIA = {
  concursos: 3802,
  janelas: [10, 50, 100],
  dezenas: DEZENAS.map((d) => ({
    dezena: d,
    total: 2200 + d,
    percentual: 60,
    janelas: { '10': 6, '50': 30, '100': 60 },
  })),
}

export const QUENTES_FRIAS = {
  janela: 50,
  concursos_na_janela: 50,
  quentes: [11, 20, 13, 5, 24].map((d, i) => ({ dezena: d, vezes: 40 - i })),
  frias: [16, 8, 3, 21, 17].map((d, i) => ({ dezena: d, vezes: 22 + i })),
}

export const ATRASOS = {
  concursos: 3802,
  dezenas: DEZENAS.map((d) => ({ dezena: d, atraso_atual: d % 4, maior_atraso: 12, ultimo_concurso: 3802 })),
}

export const DISTRIBUICAO = {
  caracteristica: 'pares',
  concursos: 3802,
  media: 7.2,
  minimo: 3,
  maximo: 11,
  valores: [
    { valor: 7, concursos: 1200, percentual: 31.56 },
    { valor: 8, concursos: 1000, percentual: 26.3 },
  ],
}

export const COMBINACOES = {
  tamanho: 2,
  concursos: 3802,
  combinacoes: [{ dezenas: [20, 25], vezes: 1500, percentual: 39.45 }],
}

export const FILTRO = {
  obrigatorias: [7],
  excluidas: [],
  concursos_analisados: 3802,
  concursos_atendidos: 2281,
  percentual: 59.99,
  ultimo_concurso_atendido: 3802,
}

export const REGRAS = [
  { codigo: 'pares', nome: 'Pares', descricao: 'Dezenas pares', parametros_padrao: { minimo: 7, maximo: 8 }, ativa: true },
  { codigo: 'soma', nome: 'Soma das dezenas', descricao: null, parametros_padrao: { minimo: 180, maximo: 220 }, ativa: true },
]

export const ESTRATEGIA = {
  id: 1,
  nome: 'Equilibrada',
  descricao: null,
  ativa: true,
  criada_em: '2026-10-12T20:00:00+00:00',
  atualizada_em: '2026-10-12T20:00:00+00:00',
  usada: true,
  regras: [{ codigo: 'pares', nome: 'Pares', minimo: 7, maximo: 8 }],
}

const PERFIL = {
  pares: 7, impares: 8, primos: 5, soma: 190, moldura: 10, miolo: 5,
  por_linha: [3, 3, 3, 3, 3], por_coluna: [3, 3, 3, 3, 3],
  maior_sequencia: 3, blocos_consecutivos: 3, fibonacci: 4, multiplos_de_3: 5,
}

export const GERACAO = {
  id: 7,
  criada_em: '2026-10-12T21:00:00+00:00',
  estrategia_id: 1,
  estrategia_nome: 'Equilibrada',
  concurso_base: 3802,
  quantidade_jogos: 2,
  dezenas_por_jogo: 15,
  obrigatorias: [10],
  excluidas: [],
  regras: [{ codigo: 'pares', nome: 'Pares', minimo: 7, maximo: 8 }],
  semente: 42,
  tentativas: 9,
  jogos: [
    { id: 70, sequencia: 1, dezenas: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], perfil: PERFIL, repetidas_do_concurso_base: 9 },
    { id: 71, sequencia: 2, dezenas: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], perfil: PERFIL, repetidas_do_concurso_base: 8 },
  ],
}
