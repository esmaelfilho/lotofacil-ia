import { describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/apiSimulada'
import { api, ErroApi, montarUrl } from './cliente'

describe('cliente da API', () => {
  it('monta a URL com /api, listas repetidas e sem valores vazios', () => {
    expect(montarUrl('/estatisticas/obrigatorias-excluidas', {
      obrigatorias: [1, 2],
      excluidas: [],
      ultimos: null,
    })).toBe('/api/estatisticas/obrigatorias-excluidas?obrigatorias=1&obrigatorias=2')
    expect(montarUrl('/concursos')).toBe('/api/concursos')
  })

  it('usa POST para atualizar', async () => {
    const fetch = simularApi({ 'POST /concursos/atualizar': { inseridos: 1 } })
    await api.atualizarConcursos()
    expect(fetch).toHaveBeenCalledWith('/api/concursos/atualizar', expect.objectContaining({ method: 'POST' }))
  })

  it('mostra a mensagem de erro que o backend mandou', async () => {
    simularApi({ '/estatisticas/obrigatorias-excluidas': { status: 422, corpo: { detail: 'dezena repetida' } } })
    await expect(api.obrigatoriasExcluidas([3, 3], [])).rejects.toThrow('dezena repetida')
  })

  it('junta as mensagens de validação do FastAPI', async () => {
    simularApi({ '/estatisticas/combinacoes': { status: 422, corpo: { detail: [{ msg: 'A' }, { msg: 'B' }] } } })
    await expect(api.combinacoes(2)).rejects.toThrow('A; B')
  })

  it('explica quando o backend está desligado', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    const erro = await api.concursos().catch((e: unknown) => e)
    expect(erro).toBeInstanceOf(ErroApi)
    expect((erro as ErroApi).message).toMatch(/uvicorn/)
    expect((erro as ErroApi).status).toBeNull()
  })

  it('erro do proxy (backend fora do ar) vira mensagem útil', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 502 }))
    await expect(api.atrasos()).rejects.toThrow(/uvicorn/)
  })
})
