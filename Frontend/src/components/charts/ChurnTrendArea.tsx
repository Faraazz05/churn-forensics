import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface ChurnTrendData {
  month: string
  churn_rate: number
  predicted: number
}

export function ChurnTrendArea({ data }: { data: ChurnTrendData[] }) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-400 font-medium mb-2">{label}</p>
          <p className="text-red-400 font-mono">Actual: {(payload[0]?.value * 100).toFixed(1)}%</p>
          <p className="text-blue-400 font-mono">Predicted: {(payload[1]?.value * 100).toFixed(1)}%</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
        <defs>
          <linearGradient id="colorChurn" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
          </linearGradient>
        </defs>
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
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="churn_rate" stroke="#EF4444" strokeWidth={2.5} fillOpacity={1} fill="url(#colorChurn)" />
        <Area type="monotone" dataKey="predicted" stroke="#3B82F6" strokeWidth={2.5} strokeDasharray="5 5" fillOpacity={1} fill="url(#colorPredicted)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
