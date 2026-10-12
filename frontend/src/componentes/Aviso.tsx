import Alert from '@mui/material/Alert'

export const TEXTO_DO_AVISO =
  'Cada sorteio é independente. As estatísticas descrevem resultados passados e não aumentam a chance de acerto.'

export default function Aviso() {
  return (
    <Alert severity="info" variant="outlined">
      {TEXTO_DO_AVISO}
    </Alert>
  )
}
