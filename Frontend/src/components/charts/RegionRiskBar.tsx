import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface RegionRiskData {
  region: string
  churn_rate: number
  count: number
}

export function RegionRiskBar({ data }: { data: RegionRiskData[] }) {
  const getColor = (rate: number) => {
    if (rate > 0.3) return '#EF4444'
    if (rate > 0.2) return '#F59E0B'
    if (rate > 0.1) return '#3B82F6'
    return '#10B981'
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-300 font-medium mb-1">{item.region}</p>
          <p className="font-bold text-base" style={{ color: getColor(item.churn_rate) }}>
            Churn: {(item.churn_rate * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-slate-500 mt-1">{item.count} customers</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2A45" vertical={false} />
        <XAxis
          dataKey="region"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
        />
        <YAxis
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141E35' }} />
        <Bar dataKey="churn_rate" radius={[6, 6, 0, 0]} maxBarSize={50}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.churn_rate)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
