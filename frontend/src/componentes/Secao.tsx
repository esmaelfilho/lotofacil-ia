import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import type { ReactNode } from 'react'

export default function Secao({
  titulo,
  descricao,
  acoes,
  children,
}: {
  titulo: string
  descricao?: string
  acoes?: ReactNode
  children: ReactNode
}) {
  return (
    <Paper variant="outlined" sx={{ p: { xs: 2, sm: 3 } }} component="section">
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={1}
        sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, mb: 2 }}
      >
        <div>
          <Typography variant="h6" component="h2">
            {titulo}
          </Typography>
          {descricao && (
            <Typography variant="body2" color="text.secondary">
              {descricao}
            </Typography>
          )}
        </div>
        {acoes}
      </Stack>
      {children}
    </Paper>
  )
}
