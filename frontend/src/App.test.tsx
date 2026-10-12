import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import App from './App'
import { TEXTO_DO_AVISO } from './componentes/Aviso'
import { simularApi } from './testes/apiSimulada'
import { IMPORTACAO, paginaConcursos } from './testes/dados'

describe('App', () => {
  it('mostra o aviso e troca de aba', async () => {
    simularApi({
      '/concursos': paginaConcursos(),
      '/importacoes': [IMPORTACAO],
      '/estatisticas/perfil': {
        total: 1,
        itens: [{
          numero: 3802, data_sorteio: '2026-10-10',
          dezenas: [1, 2, 4, 5, 7, 9, 10, 12, 14, 16, 18, 20, 22, 23, 25],
          perfil: {
            pares: 8, impares: 7, primos: 5, soma: 188, moldura: 12, miolo: 3,
            por_linha: [4, 3, 2, 3, 3], por_coluna: [3, 3, 2, 4, 3],
            maior_sequencia: 2, blocos_consecutivos: 3, fibonacci: 4, multiplos_de_3: 4,
          },
          repetidas_do_anterior: 9,
        }],
      },
    })
    const usuario = userEvent.setup()
    render(<App />)
    expect(screen.getByText(TEXTO_DO_AVISO)).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Atualizar concursos' })).toBeInTheDocument()

    await usuario.click(screen.getByRole('tab', { name: 'Perfil dos concursos' }))
    expect(await screen.findByText('188')).toBeInTheDocument()
    expect(screen.getByText(TEXTO_DO_AVISO)).toBeInTheDocument()
  })
})
