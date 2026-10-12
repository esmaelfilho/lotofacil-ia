import { describe, expect, it } from 'vitest'

import { formatarData, formatarDezena, formatarNumero } from './formatar'

describe('formatar', () => {
  it('dezena sempre com dois dígitos', () => {
    expect(formatarDezena(1)).toBe('01')
    expect(formatarDezena(25)).toBe('25')
  })

  it('data no formato brasileiro, sem erro de fuso', () => {
    expect(formatarData('2026-10-10')).toBe('10/10/2026')
    expect(formatarData('2003-09-29')).toBe('29/09/2003')
  })

  it('número com separador de milhar', () => {
    expect(formatarNumero(3802)).toBe('3.802')
  })
})
