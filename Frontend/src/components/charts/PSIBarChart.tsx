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

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2A45" horizontal={false} />
        <XAxis type="number" stroke="#64748B" />
        <YAxis dataKey="feature" type="category" stroke="#64748B" tick={{ fontSize: 12 }} width={100} />
        <Tooltip 
          cursor={{ fill: '#141E35' }}
          contentStyle={{ backgroundColor: '#0F1629', borderColor: '#1E2A45', color: '#F1F5F9', borderRadius: '8px' }} 
        />
        <ReferenceLine x={0.2} stroke="#EF4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Critical', fill: '#EF4444', fontSize: 10 }} />
        <ReferenceLine x={0.1} stroke="#F59E0B" strokeDasharray="3 3" label={{ position: 'top', value: 'Warning', fill: '#F59E0B', fontSize: 10 }} />
        <Bar dataKey="psi" radius={[0, 4, 4, 0]} maxBarSize={30}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.psi)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
