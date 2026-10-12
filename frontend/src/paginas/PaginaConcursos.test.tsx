import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { simularApi } from '../testes/apiSimulada'
import { IMPORTACAO, paginaConcursos } from '../testes/dados'
import PaginaConcursos from './PaginaConcursos'

describe('Página de concursos', () => {
  it('mostra o último concurso, a lista e o histórico', async () => {
    simularApi({ '/concursos': paginaConcursos(), '/importacoes': [IMPORTACAO] })
    render(<PaginaConcursos />)

    expect(await screen.findAllByText(/10\/10\/2026/)).toHaveLength(2) // cartão e tabela
    const bolinhas = within(screen.getAllByLabelText('dezenas')[0])
    expect(bolinhas.getByText('01')).toBeInTheDocument()
    expect(bolinhas.getByText('25')).toBeInTheDocument()
    expect(await screen.findByText('Concluída')).toBeInTheDocument()
    expect(screen.getByText(/de 3\.802/)).toBeInTheDocument()
  })

  it('botão Atualizar chama a API e mostra o resumo', async () => {
    let total = 3801
    const fetch = simularApi({
      '/concursos': () => paginaConcursos(total),
      '/importacoes': [IMPORTACAO],
      'POST /concursos/atualizar': () => {
        total = 3802
        return {
          importacao_id: 2, status: 'CONCLUIDA', ultimo_concurso_caixa: 3802,
          ultimo_concurso_banco: 3802, buscados: 1, inseridos: 1, ignorados: 0,
          rejeitados: 0, faltam: 0, mensagem: 'Banco atualizado até o concurso 3802.',
        }
      },
    })
    const usuario = userEvent.setup()
    render(<PaginaConcursos />)

    await usuario.click(await screen.findByRole('button', { name: 'Atualizar concursos' }))
    expect(await screen.findByText('1 concurso(s) inserido(s).')).toBeInTheDocument()
    expect(screen.getByText(/Banco atualizado até o concurso 3802/)).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/concursos/atualizar', expect.objectContaining({ method: 'POST' }))
    expect(await screen.findByText(/de 3\.802/)).toBeInTheDocument() // a lista recarregou
  })

  it('avisa quando ainda faltam concursos', async () => {
    simularApi({
      '/concursos': paginaConcursos(300),
      '/importacoes': [],
      'POST /concursos/atualizar': {
        importacao_id: 1, status: 'CONCLUIDA', ultimo_concurso_caixa: 3802,
        ultimo_concurso_banco: 300, buscados: 300, inseridos: 300, ignorados: 0,
        rejeitados: 0, faltam: 3502, mensagem: '',
      },
    })
    const usuario = userEvent.setup()
    render(<PaginaConcursos />)
    await usuario.click(await screen.findByRole('button', { name: 'Atualizar concursos' }))
    expect(await screen.findByText(/Ainda faltam 3\.502: clique de novo/)).toBeInTheDocument()
  })

  it('mostra o erro quando a Caixa está fora do ar', async () => {
    simularApi({
      '/concursos': paginaConcursos(),
      '/importacoes': [],
      'POST /concursos/atualizar': { status: 502, corpo: { detail: 'Não foi possível consultar a Caixa: tempo esgotado' } },
    })
    const usuario = userEvent.setup()
    render(<PaginaConcursos />)
    await usuario.click(await screen.findByRole('button', { name: 'Atualizar concursos' }))
    expect(await screen.findByText(/Não foi possível consultar a Caixa/)).toBeInTheDocument()
  })

  it('banco vazio orienta a clicar em Atualizar', async () => {
    simularApi({ '/concursos': paginaConcursos(0), '/importacoes': [] })
    render(<PaginaConcursos />)
    expect(await screen.findByText(/Nenhum concurso no banco ainda/)).toBeInTheDocument()
    expect(screen.getByText('Nenhuma atualização ainda.')).toBeInTheDocument()
  })

  it('backend desligado: mostra a orientação e permite tentar de novo', async () => {
    simularApi({ '/concursos': { status: 502, corpo: '' }, '/importacoes': { status: 502, corpo: '' } })
    render(<PaginaConcursos />)
    expect((await screen.findAllByText(/uvicorn/)).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Tentar de novo' }).length).toBeGreaterThan(0)
  })
})
