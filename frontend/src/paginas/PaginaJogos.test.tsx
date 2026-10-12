import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { simularApi } from '../testes/apiSimulada'
import { ESTRATEGIA, GERACAO, REGRAS } from '../testes/dados'
import PaginaJogos, { AVISO_GERACAO } from './PaginaJogos'

function corpoDaChamada(fetch: ReturnType<typeof simularApi>, metodo: string, caminho: string) {
  const chamada = fetch.mock.calls.find(
    ([url, opcoes]) => String(url).startsWith(`/api${caminho}`) && opcoes?.method === metodo,
  )
  return chamada ? JSON.parse(String(chamada[1]?.body)) : undefined
}

function rotas(extra: Record<string, unknown> = {}) {
  const resumo = { ...GERACAO, jogos: undefined, tentativas: undefined }
  return {
    '/regras': REGRAS,
    '/estrategias': [ESTRATEGIA, { ...ESTRATEGIA, id: 2, nome: 'Nova', usada: false, regras: [] }],
    '/geracoes': { total: 1, itens: [resumo] },
    '/geracoes/7': GERACAO,
    'POST /geracoes': GERACAO,
    ...extra,
  }
}

describe('Página de jogos', () => {
  it('mostra o aviso, as estratégias e só permite excluir as não usadas', async () => {
    simularApi(rotas())
    render(<PaginaJogos />)
    expect(screen.getByText(AVISO_GERACAO)).toBeInTheDocument()
    expect(await screen.findByText('Pares: 7 a 8')).toBeInTheDocument()
    expect(screen.getByText('já usada')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Excluir' })).toHaveLength(1)
  })

  it('cria uma estratégia com as faixas escolhidas', async () => {
    const fetch = simularApi(rotas({ 'POST /estrategias': { ...ESTRATEGIA, id: 3, nome: 'Teste' } }))
    const usuario = userEvent.setup()
    render(<PaginaJogos />)

    await usuario.click(await screen.findByRole('button', { name: 'Nova estratégia' }))
    const dialogo = await screen.findByRole('dialog')
    await usuario.type(within(dialogo).getByLabelText(/Nome/), 'Teste')
    await usuario.click(within(dialogo).getByRole('checkbox', { name: 'Pares' }))
    const minimo = within(dialogo).getByLabelText('Pares mínimo')
    await usuario.clear(minimo)
    await usuario.type(minimo, '6')
    await usuario.click(within(dialogo).getByRole('button', { name: 'Salvar' }))

    await vi.waitFor(() =>
      expect(corpoDaChamada(fetch, 'POST', '/estrategias')).toEqual({
        nome: 'Teste',
        descricao: null,
        regras: [{ codigo: 'pares', minimo: 6, maximo: 8 }],
      }),
    )
  })

  it('gera jogos, mostra a geração e confere contra um concurso', async () => {
    const fetch = simularApi(
      rotas({
        'POST /geracoes/7/conferir': {
          geracao_id: 7,
          concurso: 3802,
          dezenas_sorteadas: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
          jogos: [
            { jogo_id: 70, sequencia: 1, dezenas: GERACAO.jogos[0].dezenas, acertos: 15, dezenas_acertadas: GERACAO.jogos[0].dezenas },
            { jogo_id: 71, sequencia: 2, dezenas: GERACAO.jogos[1].dezenas, acertos: 6, dezenas_acertadas: [10, 11, 12, 13, 14, 15] },
          ],
          por_acertos: { '15': 1, '6': 1 },
        },
      }),
    )
    const usuario = userEvent.setup()
    render(<PaginaJogos />)

    await usuario.click(await screen.findByRole('button', { name: /dezena 10/ }))
    await usuario.click(screen.getByRole('button', { name: 'Gerar jogos' }))
    expect(await screen.findByText(/Geração 7/)).toBeInTheDocument()
    expect(corpoDaChamada(fetch, 'POST', '/geracoes')).toEqual({
      estrategia_id: null,
      quantidade: 5,
      dezenas_por_jogo: 15,
      obrigatorias: [10],
      excluidas: [],
      concurso_base: null,
      semente: null,
    })

    await usuario.type(screen.getByLabelText('Conferir contra o concurso'), '3802')
    await usuario.click(screen.getByRole('button', { name: 'Conferir' }))
    expect(await screen.findByText(/1 jogo\(s\) com 15 acertos/)).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Acertos' })).toBeInTheDocument()
  })

  it('mostra o erro quando as regras não permitem jogos suficientes', async () => {
    simularApi(
      rotas({
        'POST /geracoes': {
          status: 422,
          corpo: { detail: 'Só foram encontrados 0 de 5 jogos que respeitam todas as regras.' },
        },
      }),
    )
    const usuario = userEvent.setup()
    render(<PaginaJogos />)
    await usuario.click(await screen.findByRole('button', { name: 'Gerar jogos' }))
    expect(await screen.findByText(/Só foram encontrados 0 de 5/)).toBeInTheDocument()
  })

  it('confere um jogo contra o histórico', async () => {
    const fetch = simularApi(
      rotas({
        'POST /jogos/conferir-historico': {
          dezenas: GERACAO.jogos[0].dezenas,
          concursos: 3802,
          por_acertos: { '11': 400, '12': 90, '13': 10, '14': 1, '15': 0 },
          maior_acerto: 14,
          ultimo_concurso_com_11_ou_mais: 3790,
        },
      }),
    )
    const usuario = userEvent.setup()
    render(<PaginaJogos />)
    await usuario.click(await screen.findByText('Equilibrada', { selector: 'td' }))
    const botoes = await screen.findAllByRole('button', { name: 'Histórico' })
    await usuario.click(botoes[0])
    expect(await screen.findByText(/último com 11 ou mais: concurso 3790/)).toBeInTheDocument()
    expect(corpoDaChamada(fetch, 'POST', '/jogos/conferir-historico')).toEqual({
      dezenas: GERACAO.jogos[0].dezenas,
    })
  })

  it('quantidade inválida não chama a API', async () => {
    const fetch = simularApi(rotas())
    const usuario = userEvent.setup()
    render(<PaginaJogos />)
    const campo = await screen.findByLabelText('Quantos jogos')
    await usuario.clear(campo)
    await usuario.type(campo, '500')
    await usuario.click(screen.getByRole('button', { name: 'Gerar jogos' }))
    expect(await screen.findByText('A quantidade de jogos deve ser de 1 a 100.')).toBeInTheDocument()
    expect(corpoDaChamada(fetch, 'POST', '/geracoes')).toBeUndefined()
  })
})
