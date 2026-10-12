import AppBar from '@mui/material/AppBar'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import CssBaseline from '@mui/material/CssBaseline'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import Aviso from './componentes/Aviso'
import PaginaConcursos from './paginas/PaginaConcursos'
import PaginaEstatisticas from './paginas/PaginaEstatisticas'
import PaginaPerfil from './paginas/PaginaPerfil'

const tema = createTheme({
  colorSchemes: { light: true, dark: true },
  palette: { primary: { main: '#6a1b9a' }, secondary: { main: '#00897b' } },
})

const ABAS = [
  { nome: 'Concursos', Pagina: PaginaConcursos },
  { nome: 'Estatísticas', Pagina: PaginaEstatisticas },
  { nome: 'Perfil dos concursos', Pagina: PaginaPerfil },
]

export default function App() {
  const [aba, setAba] = useState(0)
  const { Pagina } = ABAS[aba]
  return (
    <ThemeProvider theme={tema}>
      <CssBaseline />
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Typography variant="h6" component="h1">
            Lotofácil IA
          </Typography>
        </Toolbar>
        <Tabs
          value={aba}
          onChange={(_, nova: number) => setAba(nova)}
          textColor="inherit"
          indicatorColor="secondary"
          variant="scrollable"
          aria-label="seções"
        >
          {ABAS.map((a) => (
            <Tab key={a.nome} label={a.nome} />
          ))}
        </Tabs>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Aviso />
        </Box>
        <Pagina />
      </Container>
    </ThemeProvider>
  )
}
