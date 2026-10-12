import Box from '@mui/material/Box'

import { formatarDezena } from '../util/formatar'

export type Marcacao = 'normal' | 'obrigatoria' | 'excluida' | 'vazia' | 'acerto' | 'apagada'

const CORES: Record<Marcacao, { fundo: string; texto: string; borda: string }> = {
  normal: { fundo: 'primary.main', texto: 'primary.contrastText', borda: 'primary.main' },
  obrigatoria: { fundo: 'success.main', texto: 'success.contrastText', borda: 'success.main' },
  excluida: { fundo: 'error.main', texto: 'error.contrastText', borda: 'error.main' },
  vazia: { fundo: 'transparent', texto: 'text.primary', borda: 'divider' },
  acerto: { fundo: 'success.main', texto: 'success.contrastText', borda: 'success.main' },
  apagada: { fundo: 'transparent', texto: 'text.secondary', borda: 'divider' },
}

interface Props {
  dezena: number
  marcacao?: Marcacao
  tamanho?: number
}

export default function Bolinha({ dezena, marcacao = 'normal', tamanho = 34 }: Props) {
  const cor = CORES[marcacao]
  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: tamanho,
        height: tamanho,
        borderRadius: '50%',
        bgcolor: cor.fundo,
        color: cor.texto,
        border: 2,
        borderColor: cor.borda,
        fontWeight: 600,
        fontSize: tamanho * 0.42,
        fontVariantNumeric: 'tabular-nums',
        textDecoration: marcacao === 'excluida' ? 'line-through' : 'none',
        flexShrink: 0,
      }}
    >
      {formatarDezena(dezena)}
    </Box>
  )
}

/** Dezenas em bolinhas. Com `destaque`, as dezenas destacadas ficam verdes e as outras apagadas. */
export function Dezenas({
  dezenas,
  tamanho,
  destaque,
}: {
  dezenas: number[]
  tamanho?: number
  destaque?: number[]
}) {
  const destacadas = destaque ? new Set(destaque) : null
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }} aria-label="dezenas">
      {dezenas.map((d) => (
        <Bolinha
          key={d}
          dezena={d}
          tamanho={tamanho}
          marcacao={destacadas ? (destacadas.has(d) ? 'acerto' : 'apagada') : 'normal'}
        />
      ))}
    </Box>
  )
}
