import Button from '@mui/material/Button'
import FormControl from '@mui/material/FormControl'
import Grid from '@mui/material/Grid'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../api/cliente'
import { CARACTERISTICAS, type Caracteristica, type DezenaVezes } from '../api/tipos'
import { useDados } from '../api/useDados'
import Bolinha, { Dezenas } from '../componentes/Bolinha'
import Estado from '../componentes/Estado'
import GraficoBarras from '../componentes/GraficoBarras'
import Secao from '../componentes/Secao'
import Volante, { alternar, type Marcadas } from '../componentes/Volante'
import { formatarDezena, formatarNumero } from '../util/formatar'

const JANELAS = [10, 50, 100] as const
type Janela = 'total' | (typeof JANELAS)[number]

function Escolha<T extends string | number>({
  valor,
  opcoes,
  aoMudar,
  rotulo,
}: {
  valor: T
  opcoes: { valor: T; nome: string }[]
  aoMudar: (v: T) => void
  rotulo: string
}) {
  return (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={valor}
      onChange={(_, novo: T | null) => novo !== null && aoMudar(novo)}
      aria-label={rotulo}
    >
      {opcoes.map((o) => (
        <ToggleButton key={o.valor} value={o.valor}>
          {o.nome}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  )
}

const OPCOES_JANELA = [
  { valor: 10, nome: 'Últimos 10' },
  { valor: 50, nome: 'Últimos 50' },
  { valor: 100, nome: 'Últimos 100' },
]

function Frequencia() {
  const [janela, setJanela] = useState<Janela>('total')
  const consulta = useDados(() => api.frequencia([...JANELAS]), [])
  return (
    <Secao
      titulo="Frequência das dezenas"
      descricao="Quantas vezes cada dezena saiu."
      acoes={
        <Escolha<Janela>
          rotulo="período da frequência"
          valor={janela}
          aoMudar={setJanela}
          opcoes={[{ valor: 'total', nome: 'Todos' }, ...OPCOES_JANELA] as { valor: Janela; nome: string }[]}
        />
      }
    >
      <Estado consulta={consulta}>
        {(f) => (
          <GraficoBarras
            dados={f.dezenas.map((d) => ({
              dezena: d.dezena,
              vezes: janela === 'total' ? d.total : d.janelas[String(janela)],
            }))}
            eixoX="dezena"
            nomeDoEixoX={(v) => formatarDezena(Number(v))}
            series={[{ chave: 'vezes', nome: 'Vezes' }]}
          />
        )}
      </Estado>
    </Secao>
  )
}

function ListaDezenas({ titulo, itens }: { titulo: string; itens: DezenaVezes[] }) {
  return (
    <Stack spacing={1}>
      <Typography variant="subtitle2">{titulo}</Typography>
      <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', rowGap: 1 }}>
        {itens.map((i) => (
          <Stack key={i.dezena} sx={{ alignItems: 'center' }}>
            <Bolinha dezena={i.dezena} tamanho={40} />
            <Typography variant="caption" color="text.secondary">
              {i.vezes}×
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  )
}

function QuentesFrias() {
  const [janela, setJanela] = useState<number>(50)
  const consulta = useDados(() => api.quentesFrias(janela, 5), [janela])
  return (
    <Secao
      titulo="Quentes e frias"
      descricao="As 5 dezenas que mais e menos saíram nos últimos N concursos."
      acoes={
        <Escolha
          rotulo="últimos N concursos"
          valor={janela}
          aoMudar={setJanela}
          opcoes={JANELAS.map((j) => ({ valor: j, nome: String(j) }))}
        />
      }
    >
      <Estado consulta={consulta}>
        {(q) => (
          <Stack spacing={2}>
            <ListaDezenas titulo="Quentes" itens={q.quentes} />
            <ListaDezenas titulo="Frias" itens={q.frias} />
          </Stack>
        )}
      </Estado>
    </Secao>
  )
}

function Atrasos() {
  const consulta = useDados(() => api.atrasos(), [])
  return (
    <Secao
      titulo="Atrasos"
      descricao="Há quantos concursos cada dezena não sai (atual) e o maior intervalo que ela já ficou sem sair."
    >
      <Estado consulta={consulta}>
        {(a) => (
          <GraficoBarras
            dados={a.dezenas}
            eixoX="dezena"
            nomeDoEixoX={(v) => formatarDezena(Number(v))}
            series={[
              { chave: 'atraso_atual', nome: 'Atraso atual' },
              { chave: 'maior_atraso', nome: 'Maior atraso', cor: 'secondary' },
            ]}
          />
        )}
      </Estado>
    </Secao>
  )
}

function Distribuicao() {
  const [caracteristica, setCaracteristica] = useState<Caracteristica>('pares')
  const consulta = useDados(() => api.distribuicao(caracteristica), [caracteristica])
  return (
    <Secao
      titulo="Distribuição"
      descricao="Em quantos concursos cada valor aconteceu."
      acoes={
        <FormControl size="small" sx={{ minWidth: 240 }}>
          <InputLabel id="caracteristica">Característica</InputLabel>
          <Select
            labelId="caracteristica"
            label="Característica"
            value={caracteristica}
            onChange={(e) => setCaracteristica(e.target.value as Caracteristica)}
          >
            {Object.entries(CARACTERISTICAS).map(([valor, nome]) => (
              <MenuItem key={valor} value={valor}>
                {nome}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      }
    >
      <Estado consulta={consulta}>
        {(d) => (
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              {formatarNumero(d.concursos)} concursos · média{' '}
              {d.media === null ? '—' : d.media.toLocaleString('pt-BR')} · mínimo{' '}
              {d.minimo ?? '—'} · máximo {d.maximo ?? '—'}
            </Typography>
            <GraficoBarras dados={d.valores} eixoX="valor" series={[{ chave: 'concursos', nome: 'Concursos' }]} />
          </Stack>
        )}
      </Estado>
    </Secao>
  )
}

function Combinacoes() {
  const [tamanho, setTamanho] = useState<2 | 3>(2)
  const consulta = useDados(() => api.combinacoes(tamanho, 10), [tamanho])
  return (
    <Secao
      titulo="Dezenas que mais saíram juntas"
      acoes={
        <Escolha<2 | 3>
          rotulo="pares ou trios"
          valor={tamanho}
          aoMudar={setTamanho}
          opcoes={[
            { valor: 2, nome: 'Pares' },
            { valor: 3, nome: 'Trios' },
          ]}
        />
      }
    >
      <Estado consulta={consulta}>
        {(c) => (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dezenas</TableCell>
                <TableCell align="right">Vezes</TableCell>
                <TableCell align="right">% dos concursos</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {c.combinacoes.map((item) => (
                <TableRow key={item.dezenas.join('-')}>
                  <TableCell>
                    <Dezenas dezenas={item.dezenas} tamanho={28} />
                  </TableCell>
                  <TableCell align="right">{formatarNumero(item.vezes)}</TableCell>
                  <TableCell align="right">{item.percentual.toLocaleString('pt-BR')}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Estado>
    </Secao>
  )
}

function ObrigatoriasExcluidas() {
  const [marcadas, setMarcadas] = useState<Marcadas>({})
  const obrigatorias = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'obrigatoria')
  const excluidas = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'excluida')
  const temFiltro = obrigatorias.length + excluidas.length > 0
  const chave = `${obrigatorias.join(',')}|${excluidas.join(',')}`
  const consulta = useDados(
    () => (temFiltro ? api.obrigatoriasExcluidas(obrigatorias, excluidas) : Promise.resolve(null)),
    [chave],
  )

  return (
    <Secao
      titulo="Obrigatórias e excluídas"
      descricao="Clique numa dezena: 1º clique = obrigatória (verde), 2º = excluída (vermelha), 3º = desmarca."
      acoes={
        <Button size="small" onClick={() => setMarcadas({})} disabled={!temFiltro}>
          Limpar
        </Button>
      }
    >
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ alignItems: { md: 'center' } }}>
        <Volante marcadas={marcadas} onAlternar={(d) => setMarcadas((m) => alternar(m, d))} />
        <div aria-live="polite">
          {!temFiltro ? (
            <Typography color="text.secondary">Marque ao menos uma dezena.</Typography>
          ) : consulta.erro ? (
            <Typography color="error">{consulta.erro}</Typography>
          ) : consulta.carregando || !consulta.dados ? (
            <Typography color="text.secondary">Calculando…</Typography>
          ) : (
            <Stack spacing={0.5}>
              <Typography variant="h4" component="p">
                {formatarNumero(consulta.dados.concursos_atendidos)}
              </Typography>
              <Typography>
                de {formatarNumero(consulta.dados.concursos_analisados)} concursos (
                {consulta.dados.percentual.toLocaleString('pt-BR')}%) tiveram todas as obrigatórias e
                nenhuma excluída.
              </Typography>
              {consulta.dados.ultimo_concurso_atendido && (
                <Typography variant="body2" color="text.secondary">
                  Último: concurso {consulta.dados.ultimo_concurso_atendido}.
                </Typography>
              )}
            </Stack>
          )}
        </div>
      </Stack>
    </Secao>
  )
}

export default function PaginaEstatisticas() {
  return (
    <Grid container spacing={3}>
      <Grid size={12}>
        <Frequencia />
      </Grid>
      <Grid size={{ xs: 12, md: 6 }}>
        <QuentesFrias />
      </Grid>
      <Grid size={{ xs: 12, md: 6 }}>
        <Combinacoes />
      </Grid>
      <Grid size={12}>
        <Atrasos />
      </Grid>
      <Grid size={12}>
        <Distribuicao />
      </Grid>
      <Grid size={12}>
        <ObrigatoriasExcluidas />
      </Grid>
    </Grid>
  )
}
