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
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../../api/cliente'
import type { Estrategia, FaixaComNome, Regra } from '../../api/tipos'
import type { Dados } from '../../api/useDados'
import Estado from '../../componentes/Estado'
import Secao from '../../componentes/Secao'
import EditorEstrategia from './EditorEstrategia'

export function textoFaixa(f: FaixaComNome): string {
  return f.minimo === f.maximo ? `${f.nome}: ${f.minimo}` : `${f.nome}: ${f.minimo} a ${f.maximo}`
}

interface Props {
  estrategias: Dados<Estrategia[]>
  regras: Regra[]
}

export default function Estrategias({ estrategias, regras }: Props) {
  const [editando, setEditando] = useState<Estrategia | 'nova' | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  async function agir(acao: () => Promise<unknown>) {
    setErro(null)
    try {
      await acao()
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    }
    estrategias.recarregar()
  }

  return (
    <Secao
      titulo="Estratégias"
      descricao="Conjuntos de regras usados para filtrar os jogos gerados."
      acoes={
        <Button variant="outlined" onClick={() => setEditando('nova')}>
          Nova estratégia
        </Button>
      }
    >
      <Stack spacing={2}>
        {erro && <Alert severity="error">{erro}</Alert>}
        <Estado consulta={estrategias}>
          {(lista) =>
            lista.length === 0 ? (
              <Typography color="text.secondary">
                Nenhuma estratégia ainda. Você também pode gerar jogos sem estratégia.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Nome</TableCell>
                      <TableCell>Regras</TableCell>
                      <TableCell>Situação</TableCell>
                      <TableCell align="right">Ações</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lista.map((e) => (
                      <TableRow key={e.id}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {e.nome}
                          </Typography>
                          {e.descricao && (
                            <Typography variant="caption" color="text.secondary">
                              {e.descricao}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                            {e.regras.length === 0 ? (
                              <Typography variant="body2" color="text.secondary">
                                sem regras
                              </Typography>
                            ) : (
                              e.regras.map((f) => <Chip key={f.codigo} size="small" label={textoFaixa(f)} />)
                            )}
                          </Stack>
                        </TableCell>
                        <TableCell>
                          {e.ativa ? 'Ativa' : 'Desativada'}
                          {e.usada && (
                            <Typography variant="caption" color="text.secondary" component="div">
                              já usada
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                          <Button size="small" onClick={() => setEditando(e)}>
                            Editar
                          </Button>
                          <Button size="small" onClick={() => agir(() => api.ativarEstrategia(e.id, !e.ativa))}>
                            {e.ativa ? 'Desativar' : 'Ativar'}
                          </Button>
                          {!e.usada && (
                            <Button
                              size="small"
                              color="error"
                              onClick={() => {
                                if (window.confirm(`Excluir a estratégia “${e.nome}”?`)) {
                                  void agir(() => api.excluirEstrategia(e.id))
                                }
                              }}
                            >
                              Excluir
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )
          }
        </Estado>
      </Stack>
      {editando && (
        <EditorEstrategia
          aberto
          regras={regras}
          estrategia={editando === 'nova' ? null : editando}
          aoFechar={() => setEditando(null)}
          aoSalvar={() => {
            setEditando(null)
            estrategias.recarregar()
          }}
        />
      )}
    </Secao>
  )
}
