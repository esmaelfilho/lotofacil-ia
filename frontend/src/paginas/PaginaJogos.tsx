import Alert from '@mui/material/Alert'
import Stack from '@mui/material/Stack'
import { useState } from 'react'

import { api } from '../api/cliente'
import type { Geracao } from '../api/tipos'
import { useDados } from '../api/useDados'
import Estado from '../componentes/Estado'
import Estrategias from './jogos/Estrategias'
import Geracoes from './jogos/Geracoes'
import GerarJogos from './jogos/GerarJogos'

export const AVISO_GERACAO =
  'Gerar jogos com filtros estatísticos não aumenta a chance de acerto: todas as combinações têm a mesma chance em cada sorteio.'

export default function PaginaJogos() {
  const regras = useDados(() => api.regras(), [])
  const estrategias = useDados(() => api.estrategias(), [])
  const [versao, setVersao] = useState(0)
  const geracoes = useDados(() => api.geracoes(50), [versao])
  const [selecionada, setSelecionada] = useState<number | null>(null)
  const [recemGerada, setRecemGerada] = useState<Geracao | null>(null)

  return (
    <Stack spacing={3}>
      <Alert severity="warning" variant="outlined">
        {AVISO_GERACAO}
      </Alert>
      <Estado consulta={regras}>
        {(catalogo) => <Estrategias estrategias={estrategias} regras={catalogo} />}
      </Estado>
      <GerarJogos
        estrategias={estrategias.dados ?? []}
        aoGerar={(g) => {
          setRecemGerada(g)
          setSelecionada(g.id)
          setVersao((v) => v + 1)
          estrategias.recarregar() // a estratégia passa a constar como usada
        }}
      />
      <Geracoes
        geracoes={geracoes}
        selecionada={selecionada}
        aoSelecionar={setSelecionada}
        recemGerada={recemGerada}
      />
    </Stack>
  )
}
