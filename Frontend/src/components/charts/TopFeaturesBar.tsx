import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

interface FeatureData {
  feature: string
  importance: number
  direction: 'risk+' | 'risk-'
}

export function TopFeaturesBar({ data }: { data: FeatureData[] }) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-300 font-medium mb-1">{item.feature}</p>
          <p className="font-bold text-base" style={{ color: item.direction === 'risk+' ? '#EF4444' : '#10B981' }}>
            Importance: {item.importance.toFixed(3)}
          </p>
          <p className="text-xs text-slate-500 mt-1">{item.direction === 'risk+' ? '↑ Increases churn risk' : '↓ Reduces churn risk'}</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 40, left: 140, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2A45" horizontal={false} />
        <XAxis
          type="number"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
        />
        <YAxis
          dataKey="feature"
          type="category"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          width={140}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141E35' }} />
        <Bar dataKey="importance" radius={[0, 6, 6, 0]} maxBarSize={24}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.direction === 'risk+' ? '#EF4444' : '#10B981'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
