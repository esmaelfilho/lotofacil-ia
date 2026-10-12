// Formatos das respostas da API (espelham backend/app/schemas).

export interface Concurso {
  id: number
  numero: number
  data_sorteio: string
  dezenas: number[]
}

export interface PaginaConcursos {
  total: number
  itens: Concurso[]
}

export interface Importacao {
  id: number
  origem: string
  referencia: string
  status: string
  total_lidos: number
  total_inseridos: number
  total_ignorados: number
  total_rejeitados: number
  mensagem_erro: string | null
  iniciada_em: string
  finalizada_em: string | null
}

export interface ResumoAtualizacao {
  importacao_id: number
  status: string
  ultimo_concurso_caixa: number
  ultimo_concurso_banco: number | null
  buscados: number
  inseridos: number
  ignorados: number
  rejeitados: number
  faltam: number
  mensagem: string
}

export interface FrequenciaDezena {
  dezena: number
  total: number
  percentual: number
  janelas: Record<string, number>
}

export interface Frequencia {
  concursos: number
  janelas: number[]
  dezenas: FrequenciaDezena[]
}

export interface DezenaVezes {
  dezena: number
  vezes: number
}

export interface QuentesFrias {
  janela: number
  concursos_na_janela: number
  quentes: DezenaVezes[]
  frias: DezenaVezes[]
}

export interface AtrasoDezena {
  dezena: number
  atraso_atual: number
  maior_atraso: number
  ultimo_concurso: number | null
}

export interface Atrasos {
  concursos: number
  dezenas: AtrasoDezena[]
}

export interface Perfil {
  pares: number
  impares: number
  primos: number
  soma: number
  moldura: number
  miolo: number
  por_linha: number[]
  por_coluna: number[]
  maior_sequencia: number
  blocos_consecutivos: number
  fibonacci: number
  multiplos_de_3: number
}

export interface PerfilConcurso {
  numero: number
  data_sorteio: string
  dezenas: number[]
  perfil: Perfil
  repetidas_do_anterior: number | null
}

export interface PaginaPerfis {
  total: number
  itens: PerfilConcurso[]
}

export interface ValorDistribuicao {
  valor: number
  concursos: number
  percentual: number
}

export interface Distribuicao {
  caracteristica: string
  concursos: number
  media: number | null
  minimo: number | null
  maximo: number | null
  valores: ValorDistribuicao[]
}

export interface FiltroDezenas {
  obrigatorias: number[]
  excluidas: number[]
  concursos_analisados: number
  concursos_atendidos: number
  percentual: number
  ultimo_concurso_atendido: number | null
}

export interface Combinacao {
  dezenas: number[]
  vezes: number
  percentual: number
}

export interface Combinacoes {
  tamanho: number
  concursos: number
  combinacoes: Combinacao[]
}

export const CARACTERISTICAS = {
  pares: 'Pares',
  impares: 'Ímpares',
  primos: 'Primos',
  soma: 'Soma das dezenas',
  moldura: 'Moldura',
  miolo: 'Miolo',
  linha_1: 'Linha 1 (01 a 05)',
  linha_2: 'Linha 2 (06 a 10)',
  linha_3: 'Linha 3 (11 a 15)',
  linha_4: 'Linha 4 (16 a 20)',
  linha_5: 'Linha 5 (21 a 25)',
  coluna_1: 'Coluna 1',
  coluna_2: 'Coluna 2',
  coluna_3: 'Coluna 3',
  coluna_4: 'Coluna 4',
  coluna_5: 'Coluna 5',
  maior_sequencia: 'Maior sequência',
  blocos_consecutivos: 'Blocos de consecutivas',
  fibonacci: 'Fibonacci',
  multiplos_de_3: 'Múltiplos de 3',
  repetidas_do_anterior: 'Repetidas do concurso anterior',
} as const

export type Caracteristica = keyof typeof CARACTERISTICAS
