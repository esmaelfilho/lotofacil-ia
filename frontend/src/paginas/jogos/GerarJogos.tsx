import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../../api/cliente'
import type { Estrategia, GeracaoPrevia } from '../../api/tipos'
import Secao from '../../componentes/Secao'
import Volante, { alternar, type Marcadas } from '../../componentes/Volante'

function inteiroOuNulo(texto: string): number | null {
  return /^\d+$/.test(texto.trim()) ? Number(texto) : null
}

interface Props {
  estrategias: Estrategia[]
  /** Recebe os jogos gerados, ainda não gravados. */
  aoGerar: (previa: GeracaoPrevia) => void
}

export default function GerarJogos({ estrategias, aoGerar }: Props) {
  const ativas = estrategias.filter((e) => e.ativa)
  const [estrategiaId, setEstrategiaId] = useState('')
  const [quantidade, setQuantidade] = useState('5')
  const [dezenas, setDezenas] = useState(15)
  const [base, setBase] = useState('')
  const [semente, setSemente] = useState('')
  const [marcadas, setMarcadas] = useState<Marcadas>({})
  const [gerando, setGerando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const obrigatorias = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'obrigatoria')
  const excluidas = Object.keys(marcadas).map(Number).filter((d) => marcadas[d] === 'excluida')

  async function gerar() {
    setErro(null)
    const qtd = inteiroOuNulo(quantidade)
    if (qtd === null || qtd < 1 || qtd > 100) {
      setErro('A quantidade de jogos deve ser de 1 a 100.')
      return
    }
    setGerando(true)
    try {
      const previa = await api.previa({
        estrategia_id: estrategiaId === '' ? null : Number(estrategiaId),
        quantidade: qtd,
        dezenas_por_jogo: dezenas,
        obrigatorias,
        excluidas,
        concurso_base: inteiroOuNulo(base),
        semente: inteiroOuNulo(semente),
      })
      aoGerar(previa)
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    } finally {
      setGerando(false)
    }
  }

  return (
    <Secao titulo="Gerar jogos" descricao="Os jogos são sorteados e só ficam os que passam em todas as regras. Depois, grave os que quiser guardar.">
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
        <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
          <FormControl size="small">
            <InputLabel id="estrategia" shrink>
              Estratégia
            </InputLabel>
            <Select
              displayEmpty
              notched
              labelId="estrategia"
              label="Estratégia"
              value={estrategiaId}
              onChange={(e) => setEstrategiaId(e.target.value)}
            >
              <MenuItem value="">Nenhuma (sem filtro)</MenuItem>
              {ativas.map((e) => (
                <MenuItem key={e.id} value={String(e.id)}>
                  {e.nome}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Quantos jogos"
              size="small"
              value={quantidade}
              onChange={(e) => setQuantidade(e.target.value)}
              helperText="1 a 100"
              slotProps={{ htmlInput: { inputMode: 'numeric' } }}
            />
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel id="dezenas">Dezenas por jogo</InputLabel>
              <Select
                labelId="dezenas"
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
          </Stack>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Concurso base"
              size="small"
              value={base}
              onChange={(e) => setBase(e.target.value)}
              helperText="Vazio = o último"
              slotProps={{ htmlInput: { inputMode: 'numeric' } }}
            />
            <TextField
              label="Semente"
              size="small"
              value={semente}
              onChange={(e) => setSemente(e.target.value)}
              helperText="Vazio = sorteada"
              slotProps={{ htmlInput: { inputMode: 'numeric' } }}
            />
          </Stack>
          {erro && <Alert severity="error">{erro}</Alert>}
          <div>
            <Button
              variant="contained"
              onClick={gerar}
              disabled={gerando}
              startIcon={gerando ? <CircularProgress size={16} color="inherit" /> : undefined}
            >
              {gerando ? 'Gerando…' : 'Gerar jogos'}
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
  )
}
