import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import Volante, { alternar, type Marcadas, proximoEstado } from './Volante'

function VolanteDeTeste() {
  const [marcadas, setMarcadas] = useState<Marcadas>({})
  return <Volante marcadas={marcadas} onAlternar={(d) => setMarcadas((m) => alternar(m, d))} />
}

describe('Volante', () => {
  it('ciclo: livre -> obrigatória -> excluída -> livre', () => {
    expect(proximoEstado(undefined)).toBe('obrigatoria')
    expect(proximoEstado('obrigatoria')).toBe('excluida')
    expect(proximoEstado('excluida')).toBeUndefined()
    expect(alternar({ 5: 'excluida', 6: 'obrigatoria' }, 5)).toEqual({ 6: 'obrigatoria' })
  })

  it('mostra as 25 dezenas e muda a marcação a cada clique', async () => {
    const usuario = userEvent.setup()
    render(<VolanteDeTeste />)
    expect(screen.getAllByRole('button')).toHaveLength(25)

    await usuario.click(screen.getByRole('button', { name: /dezena 07/ }))
    expect(screen.getByRole('button', { name: 'dezena 07: obrigatória' })).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: /dezena 07/ }))
    expect(screen.getByRole('button', { name: 'dezena 07: excluída' })).toBeInTheDocument()
    await usuario.click(screen.getByRole('button', { name: /dezena 07/ }))
    expect(screen.getByRole('button', { name: 'dezena 07: sem marcação' })).toBeInTheDocument()
  })
})
