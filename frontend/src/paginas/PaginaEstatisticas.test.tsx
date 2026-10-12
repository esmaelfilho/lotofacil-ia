import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { simularApi } from '../testes/apiSimulada'
import { ATRASOS, COMBINACOES, DISTRIBUICAO, FILTRO, FREQUENCIA, QUENTES_FRIAS } from '../testes/dados'
import PaginaEstatisticas from './PaginaEstatisticas'

function rotas() {
  return {
    '/estatisticas/frequencia': FREQUENCIA,
    '/estatisticas/quentes-frias': QUENTES_FRIAS,
    '/estatisticas/atrasos': ATRASOS,
    '/estatisticas/distribuicao': DISTRIBUICAO,
    '/estatisticas/combinacoes': COMBINACOES,
    '/estatisticas/obrigatorias-excluidas': FILTRO,
  }
}

describe('Página de estatísticas', () => {
  it('mostra quentes, frias, combinações e o resumo da distribuição', async () => {
    simularApi(rotas())
    render(<PaginaEstatisticas />)
    expect(await screen.findByText('Quentes')).toBeInTheDocument()
    expect(screen.getByText('40×')).toBeInTheDocument()
    expect(await screen.findByText('39,45%')).toBeInTheDocument()
    expect(await screen.findByText(/média 7,2 · mínimo 3 · máximo 11/)).toBeInTheDocument()
  })

  it('volante consulta obrigatórias e excluídas', async () => {
    const fetch = simularApi(rotas())
    const usuario = userEvent.setup()
    render(<PaginaEstatisticas />)
    expect(screen.getByText('Marque ao menos uma dezena.')).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: /dezena 07/ }))
    expect(await screen.findByText('2.281')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/estatisticas/obrigatorias-excluidas?obrigatorias=7',
      expect.anything(),
    )

    await usuario.click(screen.getByRole('button', { name: /dezena 07/ })) // vira excluída
    expect(fetch).toHaveBeenCalledWith(
      '/api/estatisticas/obrigatorias-excluidas?excluidas=7',
      expect.anything(),
    )

    await usuario.click(screen.getByRole('button', { name: 'Limpar' }))
    expect(screen.getByText('Marque ao menos uma dezena.')).toBeInTheDocument()
  })

  it('trocar para trios pede tamanho=3', async () => {
    const fetch = simularApi(rotas())
    const usuario = userEvent.setup()
    render(<PaginaEstatisticas />)
    await usuario.click(await screen.findByRole('button', { name: 'Trios' }))
    expect(fetch).toHaveBeenCalledWith('/api/estatisticas/combinacoes?tamanho=3&quantidade=10', expect.anything())
  })
})
