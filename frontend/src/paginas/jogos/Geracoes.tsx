import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'

import { api } from '../../api/cliente'
import type { Geracao, PaginaGeracoes } from '../../api/tipos'
import { useDados, type Dados } from '../../api/useDados'
import Estado from '../../componentes/Estado'
import Secao from '../../componentes/Secao'
import { formatarDataHora } from '../../util/formatar'
import DetalheGeracao from './DetalheGeracao'

interface Props {
  geracoes: Dados<PaginaGeracoes>
  selecionada: number | null
  aoSelecionar: (id: number) => void
  recemGerada: Geracao | null
}

export default function Geracoes({ geracoes, selecionada, aoSelecionar, recemGerada }: Props) {
  const detalhe = useDados<Geracao | null>(
    () =>
      selecionada === null
        ? Promise.resolve(null)
        : recemGerada?.id === selecionada
          ? Promise.resolve(recemGerada)
          : api.geracao(selecionada),
    [selecionada],
  )

  return (
    <Secao titulo="Jogos gravados" descricao="Clique numa geração gravada para ver os jogos e conferir com um concurso.">
      <Stack spacing={3}>
        <Estado consulta={geracoes}>
          {({ itens }) =>
            itens.length === 0 ? (
              <Typography color="text.secondary">Nenhum jogo gravado ainda.</Typography>
            ) : (
              <TableContainer sx={{ maxHeight: 280 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Geração</TableCell>
                      <TableCell>Data</TableCell>
                      <TableCell>Estratégia</TableCell>
                      <TableCell align="right">Jogos</TableCell>
                      <TableCell align="right">Base</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {itens.map((g) => (
                      <TableRow
                        key={g.id}
                        hover
                        selected={g.id === selecionada}
                        onClick={() => aoSelecionar(g.id)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>{g.id}</TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatarDataHora(g.criada_em)}</TableCell>
                        <TableCell>{g.estrategia_nome ?? '—'}</TableCell>
                        <TableCell align="right">
                          {g.quantidade_jogos} × {g.dezenas_por_jogo}
                        </TableCell>
                        <TableCell align="right">{g.concurso_base}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )
          }
        </Estado>
        {selecionada !== null && (
          <Estado consulta={detalhe}>
            {(g) => (g ? <DetalheGeracao key={g.id} geracao={g} /> : null)}
          </Estado>
        )}
      </Stack>
    </Secao>
  )
}
