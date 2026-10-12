import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { Fragment, useState } from 'react'

import { api } from '../../api/cliente'
import type { Conferencia, ConferenciaHistorico, Geracao } from '../../api/tipos'
import { Dezenas } from '../../componentes/Bolinha'
import { formatarDataHora, formatarDezena } from '../../util/formatar'
import ResultadoHistorico from './ResultadoHistorico'
import { textoFaixa } from './Estrategias'

export default function DetalheGeracao({ geracao }: { geracao: Geracao }) {
  const [numero, setNumero] = useState('')
  const [conferencia, setConferencia] = useState<Conferencia | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [historicos, setHistoricos] = useState<Record<number, ConferenciaHistorico | string>>({})

  async function conferir() {
    setErro(null)
    if (!/^\d+$/.test(numero.trim())) {
      setErro('Informe o número do concurso.')
      return
    }
    try {
      setConferencia(await api.conferir(geracao.id, Number(numero)))
    } catch (e) {
      setConferencia(null)
      setErro(e instanceof Error ? e.message : String(e))
    }
  }

  async function verHistorico(jogoId: number, dezenas: number[]) {
    try {
      const resultado = await api.conferirHistorico(dezenas)
      setHistoricos((h) => ({ ...h, [jogoId]: resultado }))
    } catch (e) {
      setHistoricos((h) => ({ ...h, [jogoId]: e instanceof Error ? e.message : String(e) }))
    }
  }

  const acertos = new Map(conferencia?.jogos.map((j) => [j.jogo_id, j]) ?? [])
  const lista = (dezenas: number[]) => dezenas.map(formatarDezena).join(' ')

  return (
    <Stack spacing={2}>
      <Stack spacing={0.5}>
        <Typography variant="subtitle1" component="h3">
          Geração {geracao.id} · {formatarDataHora(geracao.criada_em)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {geracao.quantidade_jogos} jogos de {geracao.dezenas_por_jogo} dezenas · estratégia:{' '}
          {geracao.estrategia_nome ?? 'nenhuma'} · concurso base {geracao.concurso_base} · semente{' '}
          {geracao.semente ?? '—'}
        </Typography>
        {(geracao.obrigatorias.length > 0 || geracao.excluidas.length > 0) && (
          <Typography variant="body2" color="text.secondary">
            {geracao.obrigatorias.length > 0 && `Obrigatórias: ${lista(geracao.obrigatorias)}. `}
            {geracao.excluidas.length > 0 && `Excluídas: ${lista(geracao.excluidas)}.`}
          </Typography>
        )}
        {geracao.regras.length > 0 && (
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.5 }}>
            {geracao.regras.map((f) => (
              <Chip key={f.codigo} size="small" label={textoFaixa(f)} />
            ))}
          </Stack>
        )}
      </Stack>

      <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
        <TextField
          label="Conferir contra o concurso"
          size="small"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void conferir()}
          slotProps={{ htmlInput: { inputMode: 'numeric' } }}
        />
        <Button variant="outlined" onClick={conferir}>
          Conferir
        </Button>
      </Stack>
      {erro && <Alert severity="error">{erro}</Alert>}
      {conferencia && (
        <Alert severity="info">
          Concurso {conferencia.concurso}:{' '}
          {Object.entries(conferencia.por_acertos)
            .sort(([a], [b]) => Number(b) - Number(a))
            .map(([pontos, jogos]) => `${jogos} jogo(s) com ${pontos} acertos`)
            .join(' · ')}
          . As dezenas acertadas aparecem em verde. A conferência foi registrada.
        </Alert>
      )}

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
              {conferencia && <TableCell align="right">Acertos</TableCell>}
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {geracao.jogos.map((j) => {
              const conferido = acertos.get(j.id)
              const historico = historicos[j.id]
              return (
                <Fragment key={j.id}>
                  <TableRow>
                    <TableCell>{j.sequencia}</TableCell>
                    <TableCell sx={{ minWidth: 300 }}>
                      <Dezenas dezenas={j.dezenas} tamanho={26} destaque={conferido?.dezenas_acertadas} />
                    </TableCell>
                    <TableCell align="right">{j.perfil.pares}</TableCell>
                    <TableCell align="right">{j.perfil.soma}</TableCell>
                    <TableCell align="right">{j.repetidas_do_concurso_base}</TableCell>
                    {conferencia && (
                      <TableCell align="right">
                        <strong>{conferido?.acertos ?? '—'}</strong>
                      </TableCell>
                    )}
                    <TableCell align="right">
                      <Button size="small" onClick={() => verHistorico(j.id, j.dezenas)}>
                        Histórico
                      </Button>
                    </TableCell>
                  </TableRow>
                  {historico && (
                    <TableRow>
                      <TableCell />
                      <TableCell colSpan={conferencia ? 6 : 5}>
                        {typeof historico === 'string' ? (
                          <Typography color="error">{historico}</Typography>
                        ) : (
                          <ResultadoHistorico resultado={historico} />
                        )}
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  )
}
