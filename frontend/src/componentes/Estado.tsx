import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import type { ReactNode } from 'react'

import type { Dados } from '../api/useDados'

/** Mostra "carregando", o erro (com botão para tentar de novo) ou o conteúdo. */
export default function Estado<T>({
  consulta,
  children,
}: {
  consulta: Dados<T>
  children: (dados: T) => ReactNode
}) {
  if (consulta.erro) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={consulta.recarregar}>
            Tentar de novo
          </Button>
        }
      >
        {consulta.erro}
      </Alert>
    )
  }
  if (consulta.dados === null) {
    return (
      <Box sx={{ py: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={28} aria-label="carregando" />
      </Box>
    )
  }
  return <>{children(consulta.dados)}</>
}
