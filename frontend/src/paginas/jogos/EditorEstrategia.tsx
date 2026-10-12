import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { api } from '../../api/cliente'
import type { Estrategia, Regra } from '../../api/tipos'

interface LinhaRegra {
  usar: boolean
  minimo: string
  maximo: string
}

function linhasIniciais(regras: Regra[], estrategia: Estrategia | null): Record<string, LinhaRegra> {
  const linhas: Record<string, LinhaRegra> = {}
  for (const r of regras) {
    const usada = estrategia?.regras.find((f) => f.codigo === r.codigo)
    linhas[r.codigo] = {
      usar: Boolean(usada),
      minimo: String(usada?.minimo ?? r.parametros_padrao.minimo),
      maximo: String(usada?.maximo ?? r.parametros_padrao.maximo),
    }
  }
  return linhas
}

interface Props {
  aberto: boolean
  regras: Regra[]
  estrategia: Estrategia | null // null = nova
  aoFechar: () => void
  aoSalvar: () => void
}

export default function EditorEstrategia({ aberto, regras, estrategia, aoFechar, aoSalvar }: Props) {
  const [nome, setNome] = useState(estrategia?.nome ?? '')
  const [descricao, setDescricao] = useState(estrategia?.descricao ?? '')
  const [linhas, setLinhas] = useState(() => linhasIniciais(regras, estrategia))
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)

  function mudar(codigo: string, parte: Partial<LinhaRegra>) {
    setLinhas((atual) => ({ ...atual, [codigo]: { ...atual[codigo], ...parte } }))
  }

  async function salvar() {
    setErro(null)
    const escolhidas = regras.filter((r) => linhas[r.codigo].usar)
    for (const r of escolhidas) {
      const { minimo, maximo } = linhas[r.codigo]
      if (!/^\d+$/.test(minimo) || !/^\d+$/.test(maximo)) {
        setErro(`${r.nome}: informe mínimo e máximo como números inteiros.`)
        return
      }
    }
    const entrada = {
      nome,
      descricao: descricao || null,
      regras: escolhidas.map((r) => ({
        codigo: r.codigo,
        minimo: Number(linhas[r.codigo].minimo),
        maximo: Number(linhas[r.codigo].maximo),
      })),
    }
    setSalvando(true)
    try {
      if (estrategia) await api.atualizarEstrategia(estrategia.id, entrada)
      else await api.criarEstrategia(entrada)
      aoSalvar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Dialog open={aberto} onClose={aoFechar} fullWidth maxWidth="sm">
      <DialogTitle>{estrategia ? 'Editar estratégia' : 'Nova estratégia'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <TextField
            label="Descrição (opcional)"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            multiline
            minRows={2}
          />
          <Typography variant="subtitle2">Regras</Typography>
          {estrategia?.usada && (
            <Alert severity="info">
              Esta estratégia já foi usada. As gerações antigas guardam as regras da época e não mudam.
            </Alert>
          )}
          {regras.map((r) => {
            const linha = linhas[r.codigo]
            return (
              <Stack
                key={r.codigo}
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1}
                sx={{ alignItems: { sm: 'center' } }}
              >
                <FormControlLabel
                  sx={{ flex: 1, mr: 0 }}
                  control={
                    <Checkbox checked={linha.usar} onChange={(e) => mudar(r.codigo, { usar: e.target.checked })} />
                  }
                  label={
                    <span title={r.descricao ?? undefined}>
                      {r.nome}
                    </span>
                  }
                />
                <Stack direction="row" spacing={1}>
                  <TextField
                    label="Mínimo"
                    size="small"
                    value={linha.minimo}
                    disabled={!linha.usar}
                    onChange={(e) => mudar(r.codigo, { minimo: e.target.value })}
                    sx={{ width: 96 }}
                    slotProps={{ htmlInput: { inputMode: 'numeric', 'aria-label': `${r.nome} mínimo` } }}
                  />
                  <TextField
                    label="Máximo"
                    size="small"
                    value={linha.maximo}
                    disabled={!linha.usar}
                    onChange={(e) => mudar(r.codigo, { maximo: e.target.value })}
                    sx={{ width: 96 }}
                    slotProps={{ htmlInput: { inputMode: 'numeric', 'aria-label': `${r.nome} máximo` } }}
                  />
                </Stack>
              </Stack>
            )
          })}
          {erro && <Alert severity="error">{erro}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={aoFechar}>Cancelar</Button>
        <Button variant="contained" onClick={salvar} disabled={salvando || !nome.trim()}>
          Salvar
        </Button>
      </DialogActions>
    </Dialog>
  )
}
