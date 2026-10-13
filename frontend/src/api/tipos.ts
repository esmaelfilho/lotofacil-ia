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

// ---------- Fase 4: regras, estratégias, gerações e conferência ----------

export interface Regra {
  codigo: string
  nome: string
  descricao: string | null
  parametros_padrao: { minimo: number; maximo: number }
  ativa: boolean
}

export interface Faixa {
  codigo: string
  minimo: number
  maximo: number
}

export interface FaixaComNome extends Faixa {
  nome: string
}

export interface EstrategiaEntrada {
  nome: string
  descricao?: string | null
  regras: Faixa[]
}

export interface Estrategia {
  id: number
  nome: string
  descricao: string | null
  ativa: boolean
  criada_em: string
  atualizada_em: string
  usada: boolean
  regras: FaixaComNome[]
}

export interface GeracaoEntrada {
  estrategia_id?: number | null
  quantidade: number
  dezenas_por_jogo: number
  obrigatorias: number[]
  excluidas: number[]
  concurso_base?: number | null
  semente?: number | null
  gravar?: boolean
}

export interface JogoGerado {
  id: number
  sequencia: number
  dezenas: number[]
  perfil: Perfil
  repetidas_do_concurso_base: number
}

export interface GeracaoResumo {
  id: number
  criada_em: string
  estrategia_id: number | null
  estrategia_nome: string | null
  concurso_base: number
  quantidade_jogos: number
  dezenas_por_jogo: number
  obrigatorias: number[]
  excluidas: number[]
  regras: FaixaComNome[]
  semente: number | null
}

export interface Geracao extends GeracaoResumo {
  gravada: boolean
  tentativas: number | null
  jogos: JogoGerado[]
}

/** Jogos gerados e ainda não gravados (`gravar: false`): sem id e sem data. */
export interface GeracaoPrevia extends Omit<Geracao, 'id' | 'criada_em' | 'jogos'> {
  id: null
  criada_em: null
  gravada: false
  jogos: (Omit<JogoGerado, 'id'> & { id: null })[]
}

export interface PaginaGeracoes {
  total: number
  itens: GeracaoResumo[]
}

export interface JogoConferido {
  jogo_id: number
  sequencia: number
  dezenas: number[]
  acertos: number
  dezenas_acertadas: number[]
}

export interface Conferencia {
  geracao_id: number
  concurso: number
  dezenas_sorteadas: number[]
  jogos: JogoConferido[]
  por_acertos: Record<string, number>
}

export interface ConferenciaHistorico {
  dezenas: number[]
  concursos: number
  por_acertos: Record<string, number>
  maior_acerto: number | null
  ultimo_concurso_com_11_ou_mais: number | null
}

export interface TesteEstrategiaEntrada {
  concurso: number
  estrategia_ids: number[]
  incluir_aleatorio: boolean
  quantidade: number
  dezenas_por_jogo: number
  obrigatorias: number[]
  excluidas: number[]
  semente?: number | null
}

export interface JogoTestado {
  sequencia: number
  dezenas: number[]
  acertos: number
  dezenas_acertadas: number[]
}

export interface ResultadoDoTeste {
  estrategia_id: number | null
  estrategia_nome: string | null
  regras: FaixaComNome[]
  jogos: JogoTestado[]
  maior_acerto: number | null
  media_acertos: number | null
  por_acertos: Record<string, number>
  aviso: string | null
}

export interface TesteEstrategia {
  concurso: number
  dezenas_sorteadas: number[]
  concurso_base: number
  quantidade: number
  dezenas_por_jogo: number
  obrigatorias: number[]
  excluidas: number[]
  semente: number
  resultados: ResultadoDoTeste[]
}
