import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../api/cliente'
import type { ResumoAtualizacao } from '../api/tipos'
import { useDados } from '../api/useDados'
import { Dezenas } from '../componentes/Bolinha'
import Estado from '../componentes/Estado'
import Secao from '../componentes/Secao'
import { formatarData, formatarDataHora, formatarNumero } from '../util/formatar'

const SITUACOES: Record<string, string> = {
  CONCLUIDA: 'Concluída',
  CONCLUIDA_COM_REJEICOES: 'Concluída com rejeições',
  FALHOU: 'Falhou',
  EM_ANDAMENTO: 'Em andamento',
}

function ResultadoAtualizacao({ resumo }: { resumo: ResumoAtualizacao }) {
  const severidade =
    resumo.status === 'FALHOU' ? 'error' : resumo.rejeitados > 0 ? 'warning' : 'success'
  return (
    <Alert severity={severidade}>
      <strong>
        {resumo.inseridos === 0
          ? 'Nenhum concurso novo.'
          : `${formatarNumero(resumo.inseridos)} concurso(s) inserido(s).`}
      </strong>{' '}
      {resumo.mensagem}
      {resumo.faltam > 0 && ` Ainda faltam ${formatarNumero(resumo.faltam)}: clique de novo.`}
    </Alert>
  )
}

export default function PaginaConcursos() {
  const [pagina, setPagina] = useState(0)
  const [porPagina, setPorPagina] = useState(20)
  const [versao, setVersao] = useState(0)
  const [atualizando, setAtualizando] = useState(false)
  const [resumo, setResumo] = useState<ResumoAtualizacao | null>(null)
  const [erroAtualizacao, setErroAtualizacao] = useState<string | null>(null)

  const ultimo = useDados(() => api.concursos(1, 0), [versao])
  const lista = useDados(() => api.concursos(porPagina, pagina * porPagina), [porPagina, pagina, versao])
  const historico = useDados(() => api.importacoes(10), [versao])

  async function atualizar() {
    setAtualizando(true)
    setErroAtualizacao(null)
    setResumo(null)
    try {
      setResumo(await api.atualizarConcursos())
    } catch (e) {
      setErroAtualizacao(e instanceof Error ? e.message : String(e))
    } finally {
      setAtualizando(false)
      setVersao((v) => v + 1)
    }
  }

  return (
    <Stack spacing={3}>
      <Secao
        titulo="Último concurso"
        descricao="Busca na Caixa os concursos que ainda não estão no banco."
        acoes={
          <Button
            variant="contained"
            onClick={atualizar}
            disabled={atualizando}
            startIcon={atualizando ? <CircularProgress size={16} color="inherit" /> : undefined}
          >
            {atualizando ? 'Atualizando…' : 'Atualizar concursos'}
          </Button>
        }
      >
        <Stack spacing={2}>
          {resumo && <ResultadoAtualizacao resumo={resumo} />}
          {erroAtualizacao && <Alert severity="error">{erroAtualizacao}</Alert>}
          <Estado consulta={ultimo}>
            {({ itens }) =>
              itens.length === 0 ? (
                <Typography color="text.secondary">
                  Nenhum concurso no banco ainda. Clique em “Atualizar concursos”.
                </Typography>
              ) : (
                <Stack spacing={1}>
                  <Typography>
                    Concurso <strong>{itens[0].numero}</strong> ·{' '}
                    {formatarData(itens[0].data_sorteio)}
                  </Typography>
                  <Dezenas dezenas={itens[0].dezenas} tamanho={38} />
                </Stack>
              )
            }
          </Estado>
        </Stack>
      </Secao>

      <Secao titulo="Concursos" descricao="Do mais recente para o mais antigo.">
        <Estado consulta={lista}>
          {({ total, itens }) => (
            <>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Concurso</TableCell>
                      <TableCell>Data</TableCell>
                      <TableCell>Dezenas</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {itens.map((c) => (
                      <TableRow key={c.numero} hover>
                        <TableCell>{c.numero}</TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatarData(c.data_sorteio)}</TableCell>
                        <TableCell>
                          <Dezenas dezenas={c.dezenas} tamanho={26} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={total}
                page={pagina}
                rowsPerPage={porPagina}
                rowsPerPageOptions={[10, 20, 50]}
                onPageChange={(_, nova) => setPagina(nova)}
                onRowsPerPageChange={(e) => {
                  setPorPagina(Number(e.target.value))
                  setPagina(0)
                }}
                labelRowsPerPage="Por página"
                labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${formatarNumero(count)}`}
              />
            </>
          )}
        </Estado>
      </Secao>

      <Secao titulo="Histórico de atualizações" descricao="As 10 mais recentes.">
        <Estado consulta={historico}>
          {(registros) =>
            registros.length === 0 ? (
              <Typography color="text.secondary">Nenhuma atualização ainda.</Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Início</TableCell>
                      <TableCell>Situação</TableCell>
                      <TableCell align="right">Inseridos</TableCell>
                      <TableCell align="right">Ignorados</TableCell>
                      <TableCell align="right">Rejeitados</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {registros.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatarDataHora(r.iniciada_em)}</TableCell>
                        <TableCell title={r.mensagem_erro ?? undefined}>
                          {SITUACOES[r.status] ?? r.status}
                        </TableCell>
                        <TableCell align="right">{formatarNumero(r.total_inseridos)}</TableCell>
                        <TableCell align="right">{formatarNumero(r.total_ignorados)}</TableCell>
                        <TableCell align="right">{formatarNumero(r.total_rejeitados)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )
          }
        </Estado>
      </Secao>
    </Stack>
  )
}
