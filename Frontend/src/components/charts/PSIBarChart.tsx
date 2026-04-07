import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

interface FormattedDriftProps {
  data: { feature: string; psi: number; severity: string }[]
}

export function PSIBarChart({ data }: FormattedDriftProps) {
  const getColor = (psi: number) => {
    if (psi >= 0.2) return '#EF4444'
    if (psi >= 0.1) return '#F59E0B'
    return '#10B981'
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-300 font-medium mb-1">{item.feature}</p>
          <p className="font-bold text-base" style={{ color: getColor(item.psi) }}>
            PSI: {item.psi.toFixed(3)}
          </p>
          <p className="text-xs text-slate-500 mt-1">{item.severity}</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 40, left: 120, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2A45" horizontal={false} />
        <XAxis
          type="number"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 13, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
        />
        <YAxis
          dataKey="feature"
          type="category"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 13, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          width={120}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141E35' }} />
        <ReferenceLine x={0.2} stroke="#EF4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Critical', fill: '#EF4444', fontSize: 11, fontWeight: 600 }} />
        <ReferenceLine x={0.1} stroke="#F59E0B" strokeDasharray="3 3" label={{ position: 'top', value: 'Warning', fill: '#F59E0B', fontSize: 11, fontWeight: 600 }} />
        <Bar dataKey="psi" radius={[0, 6, 6, 0]} maxBarSize={28}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.psi)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
