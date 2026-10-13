import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/apiSimulada'
import { ESTRATEGIA, GERACAO, TESTE } from '../testes/dados'
import PaginaTesteEstrategia, { AVISO_TESTE } from './PaginaTesteEstrategia'

function corpos(fetch: ReturnType<typeof simularApi>, metodo: string, caminho: string) {
  return fetch.mock.calls
    .filter(([url, opcoes]) => String(url).startsWith(`/api${caminho}`) && opcoes?.method === metodo)
    .map(([url, opcoes]) => ({ url: String(url), corpo: opcoes?.body ? JSON.parse(String(opcoes.body)) : undefined }))
}

function rotas(extra: Record<string, unknown> = {}) {
  return {
    '/estrategias': [
      ESTRATEGIA,
      { ...ESTRATEGIA, id: 2, nome: 'Desligada', ativa: false },
    ],
    '/concursos': { total: 1, itens: [{ numero: 3802, data_sorteio: '2026-10-10', dezenas: TESTE.dezenas_sorteadas }] },
    'POST /testes-estrategia': TESTE,
    ...extra,
  }
}

describe('Página Testar estratégia', () => {
  it('mostra o aviso, sugere o último concurso e lista só as estratégias ativas', async () => {
    simularApi(rotas())
    render(<PaginaTesteEstrategia />)
    expect(screen.getByText(AVISO_TESTE)).toBeInTheDocument()
    expect(await screen.findByDisplayValue('3802')).toBeInTheDocument()
    expect(await screen.findByRole('checkbox', { name: 'Equilibrada' })).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: 'Desligada' })).not.toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /aleatório/ })).toBeChecked()
  })

  it('testa as estratégias escolhidas e mostra os acertos', async () => {
    const fetch = simularApi(rotas())
    const usuario = userEvent.setup()
    render(<PaginaTesteEstrategia />)

    await usuario.click(await screen.findByRole('checkbox', { name: 'Equilibrada' }))
    const campo = await screen.findByDisplayValue('3802')
    await usuario.clear(campo)
    await usuario.type(campo, '3802')
    await usuario.click(screen.getByRole('button', { name: 'Testar' }))

    expect(await screen.findByText('Resultado no concurso 3802')).toBeInTheDocument()
    expect(screen.getByText(/com base no concurso 3801 \(o anterior\)/)).toBeInTheDocument()
    expect(corpos(fetch, 'POST', '/testes-estrategia')[0].corpo).toEqual({
      concurso: 3802,
      estrategia_ids: [1],
      incluir_aleatorio: true,
      quantidade: 5,
      dezenas_por_jogo: 15,
      obrigatorias: [],
      excluidas: [],
      semente: null,
    })

    const resumo = screen.getByRole('table', { name: 'resumo do teste' })
    const linhas = within(resumo).getAllByRole('row')
    expect(within(linhas[1]).getAllByRole('cell').map((c) => c.textContent)).toEqual([
      'Equilibrada', '2', '13', '9,5', '0', '0', '1', '0', '0',
    ])
    expect(within(linhas[2]).getByText('Sem estratégia (aleatório)')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Gravar estes jogos' })).toHaveLength(2)
  })

  it('grava os jogos de uma estratégia e já confere com o concurso testado', async () => {
    const fetch = simularApi(
      rotas({
        'POST /geracoes': GERACAO,
        'POST /geracoes/7/conferir': { geracao_id: 7, concurso: 3802, dezenas_sorteadas: [], jogos: [], por_acertos: {} },
      }),
    )
    const usuario = userEvent.setup()
    render(<PaginaTesteEstrategia />)
    await screen.findByDisplayValue('3802')
    await usuario.click(screen.getByRole('button', { name: 'Testar' }))
    const botoes = await screen.findAllByRole('button', { name: 'Gravar estes jogos' })
    await usuario.click(botoes[0])

    expect(await screen.findByText(/gravados como geração 7 e já conferidos com o concurso 3802/)).toBeInTheDocument()
    expect(corpos(fetch, 'POST', '/geracoes')[0].corpo).toEqual({
      estrategia_id: 1,
      quantidade: 2,
      dezenas_por_jogo: 15,
      obrigatorias: [],
      excluidas: [],
      concurso_base: 3801,
      semente: 42,
      gravar: true,
    })
    await vi.waitFor(() =>
      expect(corpos(fetch, 'POST', '/geracoes/7/conferir')[0].url).toContain('concurso=3802'),
    )
    expect(screen.getByRole('button', { name: 'Gravados' })).toBeDisabled()
  })

  it('sem estratégia e sem aleatório não chama a API', async () => {
    const fetch = simularApi(rotas())
    const usuario = userEvent.setup()
    render(<PaginaTesteEstrategia />)
    await usuario.click(await screen.findByRole('checkbox', { name: /aleatório/ }))
    await usuario.click(screen.getByRole('button', { name: 'Testar' }))
    expect(await screen.findByText('Escolha pelo menos uma estratégia ou os jogos aleatórios.')).toBeInTheDocument()
    expect(corpos(fetch, 'POST', '/testes-estrategia')).toHaveLength(0)
  })

  it('mostra o erro da API', async () => {
    simularApi(
      rotas({
        'POST /testes-estrategia': { status: 404, corpo: { detail: 'Concurso 9999 não está no banco.' } },
      }),
    )
    const usuario = userEvent.setup()
    render(<PaginaTesteEstrategia />)
    const campo = await screen.findByDisplayValue('3802')
    await usuario.clear(campo)
    await usuario.type(campo, '9999')
    await usuario.click(screen.getByRole('button', { name: 'Testar' }))
    expect(await screen.findByText('Concurso 9999 não está no banco.')).toBeInTheDocument()
  })
})
