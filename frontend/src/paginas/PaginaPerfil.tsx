import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import { useState } from 'react'

import { api } from '../api/cliente'
import type { Perfil } from '../api/tipos'
import { useDados } from '../api/useDados'
import { Dezenas } from '../componentes/Bolinha'
import Estado from '../componentes/Estado'
import Secao from '../componentes/Secao'
import { formatarData, formatarNumero } from '../util/formatar'

const COLUNAS: { chave: keyof Perfil; titulo: string; dica: string }[] = [
  { chave: 'pares', titulo: 'Pares', dica: 'Dezenas pares' },
  { chave: 'impares', titulo: 'Ímpares', dica: 'Dezenas ímpares' },
  { chave: 'primos', titulo: 'Primos', dica: '02 03 05 07 11 13 17 19 23' },
  { chave: 'soma', titulo: 'Soma', dica: 'Soma das 15 dezenas' },
  { chave: 'moldura', titulo: 'Moldura', dica: 'As 16 dezenas da borda do volante' },
  { chave: 'miolo', titulo: 'Miolo', dica: '07 08 09 12 13 14 17 18 19' },
  { chave: 'maior_sequencia', titulo: 'Maior seq.', dica: 'Maior trecho de dezenas consecutivas' },
  { chave: 'fibonacci', titulo: 'Fibonacci', dica: '01 02 03 05 08 13 21' },
  { chave: 'multiplos_de_3', titulo: 'Múlt. 3', dica: '03 06 09 12 15 18 21 24' },
]

export default function PaginaPerfil() {
  const [pagina, setPagina] = useState(0)
  const [porPagina, setPorPagina] = useState(20)
  const perfis = useDados(() => api.perfis(porPagina, pagina * porPagina), [porPagina, pagina])

  return (
    <Secao
      titulo="Perfil dos concursos"
      descricao="Características de cada resultado. Passe o mouse sobre o título da coluna para ver a definição."
    >
      <Estado consulta={perfis}>
        {({ total, itens }) => (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Concurso</TableCell>
                    <TableCell>Data</TableCell>
                    <TableCell>Dezenas</TableCell>
                    {COLUNAS.map((c) => (
                      <TableCell key={c.chave} align="right" title={c.dica}>
                        {c.titulo}
                      </TableCell>
                    ))}
                    <TableCell align="right" title="Dezenas que também saíram no concurso anterior">
                      Repetidas
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {itens.map((c) => (
                    <TableRow key={c.numero} hover>
                      <TableCell>{c.numero}</TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatarData(c.data_sorteio)}</TableCell>
                      <TableCell sx={{ minWidth: 260 }}>
                        <Dezenas dezenas={c.dezenas} tamanho={22} />
                      </TableCell>
                      {COLUNAS.map((col) => (
                        <TableCell key={col.chave} align="right">
                          {String(c.perfil[col.chave])}
                        </TableCell>
                      ))}
                      <TableCell align="right">{c.repetidas_do_anterior ?? '—'}</TableCell>
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
  )
}
