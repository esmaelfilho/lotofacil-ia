import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../../api/cliente'
import type { Geracao, GeracaoPrevia } from '../../api/tipos'
import { Dezenas } from '../../componentes/Bolinha'
import Secao from '../../componentes/Secao'
import { textoFaixa } from './Estrategias'

interface Props {
  previa: GeracaoPrevia
  aoGravar: (geracao: Geracao) => void
  aoDescartar: () => void
}

/** Jogos gerados e ainda não gravados. "Gravar jogos" grava exatamente estes jogos. */
export default function PreviaJogos({ previa, aoGravar, aoDescartar }: Props) {
  const [gravando, setGravando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function gravar() {
    setErro(null)
    setGravando(true)
    try {
      // mesma semente, mesma base e mesmos parâmetros: o backend repete os mesmos jogos
      aoGravar(
        await api.gerar({
          estrategia_id: previa.estrategia_id,
          quantidade: previa.quantidade_jogos,
          dezenas_por_jogo: previa.dezenas_por_jogo,
          obrigatorias: previa.obrigatorias,
          excluidas: previa.excluidas,
          concurso_base: previa.concurso_base,
          semente: previa.semente,
        }),
      )
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    } finally {
      setGravando(false)
    }
  }

  return (
    <Secao
      titulo="Jogos gerados (não gravados)"
      descricao={`${previa.quantidade_jogos} jogos de ${previa.dezenas_por_jogo} dezenas · estratégia: ${previa.estrategia_nome ?? 'nenhuma'} · concurso base ${previa.concurso_base} · semente ${previa.semente}`}
      acoes={
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            onClick={gravar}
            disabled={gravando}
            startIcon={gravando ? <CircularProgress size={16} color="inherit" /> : undefined}
          >
            {gravando ? 'Gravando…' : 'Gravar jogos'}
          </Button>
          <Button onClick={aoDescartar} disabled={gravando}>
            Descartar
          </Button>
        </Stack>
      }
    >
      <Stack spacing={2}>
        <Alert severity="info">
          Estes jogos ainda não foram gravados. Clique em “Gravar jogos” para guardá-los e
          conferir depois; se gerar de novo sem gravar, eles são descartados.
        </Alert>
        {previa.regras.length > 0 && (
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.5 }}>
            {previa.regras.map((f) => (
              <Chip key={f.codigo} size="small" label={textoFaixa(f)} />
            ))}
          </Stack>
        )}
        {erro && <Alert severity="error">{erro}</Alert>}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Dezenas</TableCell>
                <TableCell align="right">Pares</TableCell>
                <TableCell align="right">Soma</TableCell>
                <TableCell align="right" title="Dezenas que saíram no concurso base">
                  Rep. base
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {previa.jogos.map((j) => (
                <TableRow key={j.sequencia}>
                  <TableCell>{j.sequencia}</TableCell>
                  <TableCell sx={{ minWidth: 300 }}>
                    <Dezenas dezenas={j.dezenas} tamanho={26} />
                  </TableCell>
                  <TableCell align="right">{j.perfil.pares}</TableCell>
                  <TableCell align="right">{j.perfil.soma}</TableCell>
                  <TableCell align="right">{j.repetidas_do_concurso_base}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        {previa.tentativas !== null && (
          <Typography variant="caption" color="text.secondary">
            {previa.tentativas.toLocaleString('pt-BR')} tentativas para achar estes jogos.
          </Typography>
        )}
      </Stack>
    </Secao>
  )
}
