import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface RevenueData {
  month: string
  at_risk: number
  recovered: number
}

export function RevenueImpactBar({ data }: { data: RevenueData[] }) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-400 font-medium mb-2">{label}</p>
          <p className="text-red-400 font-mono">At Risk: ${(payload[0]?.value / 1000).toFixed(0)}K</p>
          <p className="text-emerald-400 font-mono">Recovered: ${(payload[1]?.value / 1000).toFixed(0)}K</p>
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
          dataKey="month"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
        />
        <YAxis
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 12 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141E35' }} />
        <Bar dataKey="at_risk" stackId="a" fill="#EF4444" radius={[0, 0, 0, 0]} maxBarSize={35} />
        <Bar dataKey="recovered" stackId="a" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={35} />
      </BarChart>
    </ResponsiveContainer>
  )
}
