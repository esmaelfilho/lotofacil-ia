import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'

import { formatarDezena } from '../util/formatar'
import Bolinha from './Bolinha'

export type EstadoDezena = 'obrigatoria' | 'excluida'
export type Marcadas = Record<number, EstadoDezena>

const NOMES: Record<EstadoDezena | 'livre', string> = {
  livre: 'sem marcação',
  obrigatoria: 'obrigatória',
  excluida: 'excluída',
}

/** Sem marcação -> obrigatória -> excluída -> sem marcação. */
export function proximoEstado(atual: EstadoDezena | undefined): EstadoDezena | undefined {
  if (atual === undefined) return 'obrigatoria'
  if (atual === 'obrigatoria') return 'excluida'
  return undefined
}

export function alternar(marcadas: Marcadas, dezena: number): Marcadas {
  const novo = { ...marcadas }
  const estado = proximoEstado(marcadas[dezena])
  if (estado) novo[dezena] = estado
  else delete novo[dezena]
  return novo
}

interface Props {
  marcadas: Marcadas
  onAlternar: (dezena: number) => void
}

/** Volante 5×5 da Lotofácil. Cada clique muda a marcação da dezena. */
export default function Volante({ marcadas, onAlternar }: Props) {
  return (
    <Box
      role="group"
      aria-label="volante"
      sx={{ display: 'grid', gridTemplateColumns: 'repeat(5, max-content)', gap: 0.75 }}
    >
      {Array.from({ length: 25 }, (_, i) => i + 1).map((d) => {
        const estado = marcadas[d]
        return (
          <ButtonBase
            key={d}
            onClick={() => onAlternar(d)}
            aria-label={`dezena ${formatarDezena(d)}: ${NOMES[estado ?? 'livre']}`}
            sx={{ borderRadius: '50%' }}
          >
            <Bolinha dezena={d} marcacao={estado ?? 'vazia'} tamanho={40} />
          </ButtonBase>
        )
      })}
    </Box>
  )
}
