import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import FormControl from '@mui/material/FormControl'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormGroup from '@mui/material/FormGroup'
import FormLabel from '@mui/material/FormLabel'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useEffect, useState } from 'react'

import { api } from '../api/cliente'
import type { ResultadoDoTeste, TesteEstrategia } from '../api/tipos'
import { useDados } from '../api/useDados'
import { Dezenas } from '../componentes/Bolinha'
import Secao from '../componentes/Secao'
import Volante, { alternar, type Marcadas } from '../componentes/Volante'
import { textoFaixa } from './jogos/Estrategias'

export const AVISO_TESTE =
  'O teste mostra o que teria acontecido em um concurso que já saiu. Cada sorteio é independente: um bom resultado no passado não aumenta a chance no próximo.'

const PONTOS = ['11', '12', '13', '14', '15']

function inteiroOuNulo(texto: string): number | null {
  return /^\d+$/.test(texto.trim()) ? Number(texto) : null
}

function nome(r: ResultadoDoTeste) {
  return r.estrategia_nome ?? 'Sem estratégia (aleatório)'
}

export default function PaginaTesteEstrategia() {
  const estrategias = useDados(() => api.estrategias(), [])
  const ultimo = useDados(() => api.concursos(1), [])
  const ativas = (estrategias.dados ?? []).filter((e) => e.ativa)

  const [concurso, setConcurso] = useState('')
  const [escolhidas, setEscolhidas] = useState<number[]>([])
  const [aleatorio, setAleatorio] = useState(true)
  const [quantidade, setQuantidade] = useState('5')
  const [dezenas, setDezenas] = useState(15)
  const [semente, setSemente] = useState('')
  const [marcadas, setMarcadas] = useState<Marcadas>({})
  const [testando, setTestando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [teste, setTeste] = useState<TesteEstrategia | null>(null)

  // sugere o último concurso do banco
  const ultimoNumero = ultimo.dados?.itens[0]?.numero
  useEffect(() => {
    if (ultimoNumero !== undefined) setConcurso((atual) => atual || String(ultimoNumero))
  }, [ultimoNumero])

  const obrigatorias = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'obrigatoria')
  const excluidas = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'excluida')

  function alternarEstrategia(id: number) {
    setEscolhidas((atual) => (atual.includes(id) ? atual.filter((x) => x !== id) : [...atual, id]))
  }

  async function testar() {
    setErro(null)
    const numero = inteiroOuNulo(concurso)
    const qtd = inteiroOuNulo(quantidade)
    if (numero === null) {
      setErro('Informe o número do concurso a testar.')
      return
    }
    if (qtd === null || qtd < 1 || qtd > 100) {
      setErro('A quantidade de jogos deve ser de 1 a 100.')
      return
    }
    if (escolhidas.length === 0 && !aleatorio) {
      setErro('Escolha pelo menos uma estratégia ou os jogos aleatórios.')
      return
    }
    setTestando(true)
    try {
      setTeste(
        await api.testarEstrategias({
          concurso: numero,
          estrategia_ids: escolhidas,
          incluir_aleatorio: aleatorio,
          quantidade: qtd,
          dezenas_por_jogo: dezenas,
          obrigatorias,
          excluidas,
          semente: inteiroOuNulo(semente),
        }),
      )
    } catch (e) {
      setTeste(null)
      setErro(e instanceof Error ? e.message : String(e))
    } finally {
      setTestando(false)
    }
  }

  return (
    <Stack spacing={3}>
      <Alert severity="warning" variant="outlined">
        {AVISO_TESTE}
      </Alert>
      <Secao
        titulo="Testar estratégia"
        descricao="Escolha um concurso que já saiu. Os jogos são gerados como se fosse a véspera (com base no concurso anterior) e conferidos com o resultado."
      >
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
          <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
            <Stack direction="row" spacing={2}>
              <TextField
                label="Concurso a testar"
                size="small"
                value={concurso}
                onChange={(e) => setConcurso(e.target.value)}
                slotProps={{ htmlInput: { inputMode: 'numeric' } }}
              />
              <TextField
                label="Quantos jogos"
                size="small"
                value={quantidade}
                onChange={(e) => setQuantidade(e.target.value)}
                helperText="1 a 100 por estratégia"
                slotProps={{ htmlInput: { inputMode: 'numeric' } }}
              />
            </Stack>
            <Stack direction="row" spacing={2}>
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel id="teste-dezenas">Dezenas por jogo</InputLabel>
                <Select
                  labelId="teste-dezenas"
                  label="Dezenas por jogo"
                  value={dezenas}
                  onChange={(e) => setDezenas(Number(e.target.value))}
                >
                  {[15, 16, 17, 18, 19, 20].map((n) => (
                    <MenuItem key={n} value={n}>
                      {n}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Semente"
                size="small"
                value={semente}
                onChange={(e) => setSemente(e.target.value)}
                helperText="Vazio = sorteada"
                slotProps={{ htmlInput: { inputMode: 'numeric' } }}
              />
            </Stack>
            <FormControl component="fieldset">
              <FormLabel component="legend">Estratégias a testar</FormLabel>
              <FormGroup>
                {ativas.map((e) => (
                  <FormControlLabel
                    key={e.id}
                    label={e.nome}
                    control={
                      <Checkbox
                        size="small"
                        checked={escolhidas.includes(e.id)}
                        onChange={() => alternarEstrategia(e.id)}
                      />
                    }
                  />
                ))}
                <FormControlLabel
                  label="Sem estratégia (aleatório), para comparar"
                  control={
                    <Checkbox size="small" checked={aleatorio} onChange={(e) => setAleatorio(e.target.checked)} />
                  }
                />
              </FormGroup>
              {estrategias.dados && ativas.length === 0 && (
                <Typography variant="caption" color="text.secondary">
                  Nenhuma estratégia ativa. Crie uma na aba Jogos.
                </Typography>
              )}
            </FormControl>
            {erro && <Alert severity="error">{erro}</Alert>}
            <div>
              <Button
                variant="contained"
                onClick={testar}
                disabled={testando}
                startIcon={testando ? <CircularProgress size={16} color="inherit" /> : undefined}
              >
                {testando ? 'Testando…' : 'Testar'}
              </Button>
            </div>
          </Stack>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Obrigatórias e excluídas</Typography>
            <Typography variant="caption" color="text.secondary">
              1º clique = obrigatória (verde), 2º = excluída (vermelha), 3º = desmarca.
            </Typography>
            <Volante marcadas={marcadas} onAlternar={(d) => setMarcadas((m) => alternar(m, d))} />
          </Stack>
        </Stack>
      </Secao>
      {teste && <ResultadoTeste key={`${teste.concurso}-${teste.semente}`} teste={teste} />}
    </Stack>
  )
}

function ResultadoTeste({ teste }: { teste: TesteEstrategia }) {
  return (
    <Stack spacing={3}>
      <Secao
        titulo={`Resultado no concurso ${teste.concurso}`}
        descricao={`Jogos gerados com base no concurso ${teste.concurso_base} (o anterior) · ${teste.quantidade} jogos de ${teste.dezenas_por_jogo} dezenas por estratégia · semente ${teste.semente}`}
      >
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography variant="subtitle2">Dezenas sorteadas</Typography>
            <Dezenas dezenas={teste.dezenas_sorteadas} tamanho={30} />
          </Stack>
          <TableContainer>
            <Table size="small" aria-label="resumo do teste">
              <TableHead>
                <TableRow>
                  <TableCell>Estratégia</TableCell>
                  <TableCell align="right">Jogos</TableCell>
                  <TableCell align="right">Maior acerto</TableCell>
                  <TableCell align="right">Média</TableCell>
                  {PONTOS.map((p) => (
                    <TableCell key={p} align="right">
                      {p} pts
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {teste.resultados.map((r) => (
                  <TableRow key={r.estrategia_id ?? 'aleatorio'}>
                    <TableCell>{nome(r)}</TableCell>
                    <TableCell align="right">{r.jogos.length}</TableCell>
                    <TableCell align="right">{r.maior_acerto ?? '—'}</TableCell>
                    <TableCell align="right">
                      {r.media_acertos?.toLocaleString('pt-BR', { maximumFractionDigits: 2 }) ?? '—'}
                    </TableCell>
                    {PONTOS.map((p) => (
                      <TableCell key={p} align="right">
                        {r.por_acertos[p] ?? 0}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Stack>
      </Secao>
      {teste.resultados.map((r) => (
        <JogosDoTeste key={r.estrategia_id ?? 'aleatorio'} teste={teste} resultado={r} />
      ))}
    </Stack>
  )
}

function JogosDoTeste({ teste, resultado }: { teste: TesteEstrategia; resultado: ResultadoDoTeste }) {
  const [gravando, setGravando] = useState(false)
  const [gravada, setGravada] = useState<number | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  async function gravar() {
    setErro(null)
    setGravando(true)
    try {
      // mesmos parâmetros, semente e base do teste: o backend grava exatamente estes jogos
      const geracao = await api.gerar({
        estrategia_id: resultado.estrategia_id,
        quantidade: teste.quantidade,
        dezenas_por_jogo: teste.dezenas_por_jogo,
        obrigatorias: teste.obrigatorias,
        excluidas: teste.excluidas,
        concurso_base: teste.concurso_base,
        semente: teste.semente,
      })
      await api.conferir(geracao.id, teste.concurso)
      setGravada(geracao.id)
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    } finally {
      setGravando(false)
    }
  }

  const completo = resultado.jogos.length === teste.quantidade

  return (
    <Secao
      titulo={nome(resultado)}
      acoes={
        completo && (
          <Button
            variant="outlined"
            onClick={gravar}
            disabled={gravando || gravada !== null}
            startIcon={gravando ? <CircularProgress size={16} color="inherit" /> : undefined}
          >
            {gravada !== null ? 'Gravados' : gravando ? 'Gravando…' : 'Gravar estes jogos'}
          </Button>
        )
      }
    >
      <Stack spacing={2}>
        {resultado.regras.length > 0 && (
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.5 }}>
            {resultado.regras.map((f) => (
              <Chip key={f.codigo} size="small" label={textoFaixa(f)} />
            ))}
          </Stack>
        )}
        {resultado.aviso && <Alert severity="warning">{resultado.aviso}</Alert>}
        {gravada !== null && (
          <Alert severity="success">
            Jogos gravados como geração {gravada} e já conferidos com o concurso {teste.concurso}.
            Eles aparecem em “Jogos gravados”, na aba Jogos.
          </Alert>
        )}
        {erro && <Alert severity="error">{erro}</Alert>}
        {resultado.jogos.length > 0 && (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>Dezenas (acertos em verde)</TableCell>
                  <TableCell align="right">Acertos</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {resultado.jogos.map((j) => (
                  <TableRow key={j.sequencia}>
                    <TableCell>{j.sequencia}</TableCell>
                    <TableCell sx={{ minWidth: 300 }}>
                      <Dezenas dezenas={j.dezenas} tamanho={26} destaque={j.dezenas_acertadas} />
                    </TableCell>
                    <TableCell align="right">
                      <strong>{j.acertos}</strong>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Stack>
    </Secao>
  )
}
