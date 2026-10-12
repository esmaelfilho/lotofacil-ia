import { vi } from 'vitest'

export interface RespostaSimulada {
  status?: number
  corpo: unknown
}

type Rota = unknown | RespostaSimulada | ((url: URL, metodo: string) => unknown | RespostaSimulada)

function ehResposta(valor: unknown): valor is RespostaSimulada {
  return typeof valor === 'object' && valor !== null && 'corpo' in valor
}

/**
 * Substitui o fetch do navegador. `rotas` liga "MÉTODO /caminho" (ou só "/caminho" para GET)
 * à resposta. Devolve o mock, para conferir as chamadas feitas.
 */
export function simularApi(rotas: Record<string, Rota>) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (entrada, opcoes) => {
    const url = new URL(String(entrada), 'http://localhost')
    const metodo = opcoes?.method ?? 'GET'
    const caminho = url.pathname.replace(/^\/api/, '')
    const rota = rotas[`${metodo} ${caminho}`] ?? (metodo === 'GET' ? rotas[caminho] : undefined)
    if (rota === undefined) throw new Error(`rota não simulada: ${metodo} ${caminho}`)
    const valor = typeof rota === 'function' ? rota(url, metodo) : rota
    const resposta: RespostaSimulada = ehResposta(valor) ? valor : { corpo: valor }
    return new Response(JSON.stringify(resposta.corpo), {
      status: resposta.status ?? 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })
}
