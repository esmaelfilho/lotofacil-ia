// Chamadas à API do backend. Todas passam por /api, que o Vite repassa ao backend.
import type {
  Atrasos,
  Caracteristica,
  Combinacoes,
  Distribuicao,
  FiltroDezenas,
  Frequencia,
  Importacao,
  PaginaConcursos,
  PaginaPerfis,
  QuentesFrias,
  ResumoAtualizacao,
} from './tipos'

const BASE = '/api'

export class ErroApi extends Error {
  readonly status: number | null

  constructor(mensagem: string, status: number | null) {
    super(mensagem)
    this.name = 'ErroApi'
    this.status = status
  }
}

type Parametro = string | number | number[] | null | undefined

export function montarUrl(caminho: string, parametros: Record<string, Parametro> = {}): string {
  const busca = new URLSearchParams()
  for (const [nome, valor] of Object.entries(parametros)) {
    if (valor === null || valor === undefined) continue
    if (Array.isArray(valor)) valor.forEach((v) => busca.append(nome, String(v)))
    else busca.append(nome, String(valor))
  }
  const texto = busca.toString()
  return `${BASE}${caminho}${texto ? `?${texto}` : ''}`
}

function mensagemDoErro(corpo: unknown, status: number): string {
  const detalhe = (corpo as { detail?: unknown } | null)?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) {
    return detalhe.map((d) => (d as { msg?: string }).msg ?? String(d)).join('; ')
  }
  if (status === 500 || status === 502 || status === 503 || status === 504) {
    return 'O backend não respondeu. Confira se o uvicorn está rodando e se o banco está ligado.'
  }
  return `A API respondeu com erro ${status}.`
}

async function pedir<T>(url: string, metodo: 'GET' | 'POST' = 'GET'): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(url, { method: metodo, headers: { Accept: 'application/json' } })
  } catch {
    throw new ErroApi(
      'Não foi possível falar com a API. Confira se o backend (uvicorn) está rodando.',
      null,
    )
  }
  const corpo: unknown = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new ErroApi(mensagemDoErro(corpo, resposta.status), resposta.status)
  return corpo as T
}

export const api = {
  concursos: (limite = 20, deslocamento = 0) =>
    pedir<PaginaConcursos>(montarUrl('/concursos', { limite, deslocamento })),
  atualizarConcursos: () => pedir<ResumoAtualizacao>(montarUrl('/concursos/atualizar'), 'POST'),
  importacoes: (limite = 10) => pedir<Importacao[]>(montarUrl('/importacoes', { limite })),
  frequencia: (janelas: number[] = [10, 50, 100]) =>
    pedir<Frequencia>(montarUrl('/estatisticas/frequencia', { janelas })),
  quentesFrias: (janela = 50, quantidade = 5) =>
    pedir<QuentesFrias>(montarUrl('/estatisticas/quentes-frias', { janela, quantidade })),
  atrasos: () => pedir<Atrasos>(montarUrl('/estatisticas/atrasos')),
  perfis: (limite = 20, deslocamento = 0) =>
    pedir<PaginaPerfis>(montarUrl('/estatisticas/perfil', { limite, deslocamento })),
  distribuicao: (caracteristica: Caracteristica, ultimos?: number | null) =>
    pedir<Distribuicao>(montarUrl('/estatisticas/distribuicao', { caracteristica, ultimos })),
  obrigatoriasExcluidas: (obrigatorias: number[], excluidas: number[], ultimos?: number | null) =>
    pedir<FiltroDezenas>(
      montarUrl('/estatisticas/obrigatorias-excluidas', { obrigatorias, excluidas, ultimos }),
    ),
  combinacoes: (tamanho: 2 | 3, quantidade = 10, ultimos?: number | null) =>
    pedir<Combinacoes>(montarUrl('/estatisticas/combinacoes', { tamanho, quantidade, ultimos })),
}
