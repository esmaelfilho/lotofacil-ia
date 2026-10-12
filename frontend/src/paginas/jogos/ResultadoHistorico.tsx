import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'

import type { ConferenciaHistorico } from '../../api/tipos'
import { formatarNumero } from '../../util/formatar'

export default function ResultadoHistorico({ resultado }: { resultado: ConferenciaHistorico }) {
  return (
    <Stack spacing={0.5}>
      <Typography variant="body2">
        Em {formatarNumero(resultado.concursos)} concursos, este jogo teria feito:
      </Typography>
      <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
        {[15, 14, 13, 12, 11].map((p) => (
          <Typography key={p} variant="body2">
            <strong>{p} pontos:</strong> {formatarNumero(resultado.por_acertos[String(p)] ?? 0)}×
          </Typography>
        ))}
      </Stack>
      <Typography variant="caption" color="text.secondary">
        Maior acerto: {resultado.maior_acerto ?? '—'}
        {resultado.ultimo_concurso_com_11_ou_mais
          ? ` · último com 11 ou mais: concurso ${resultado.ultimo_concurso_com_11_ou_mais}`
          : ''}
      </Typography>
    </Stack>
  )
}
