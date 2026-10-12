import { useTheme } from '@mui/material/styles'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export interface Serie {
  chave: string
  nome: string
  cor?: 'primary' | 'secondary'
}

interface Props {
  dados: object[]
  eixoX: string
  series: Serie[]
  nomeDoEixoX?: (valor: unknown) => string
  altura?: number
}

export default function GraficoBarras({
  dados,
  eixoX,
  series,
  nomeDoEixoX = (v) => String(v),
  altura = 280,
}: Props) {
  const tema = useTheme()
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={dados} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={tema.palette.divider} />
        <XAxis
          dataKey={eixoX}
          tickFormatter={nomeDoEixoX}
          tick={{ fill: tema.palette.text.secondary, fontSize: 12 }}
          interval={0}
        />
        <YAxis allowDecimals={false} tick={{ fill: tema.palette.text.secondary, fontSize: 12 }} />
        <Tooltip
          labelFormatter={nomeDoEixoX}
          contentStyle={{
            background: tema.palette.background.paper,
            border: `1px solid ${tema.palette.divider}`,
          }}
          cursor={{ fill: tema.palette.action.hover }}
        />
        {series.length > 1 && <Legend />}
        {series.map((s) => (
          <Bar
            key={s.chave}
            dataKey={s.chave}
            name={s.nome}
            fill={tema.palette[s.cor ?? 'primary'].main}
            radius={[3, 3, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
