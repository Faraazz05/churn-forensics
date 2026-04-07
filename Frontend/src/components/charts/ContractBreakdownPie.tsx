import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

interface ContractData {
  plan: string
  count: number
  churn_rate: number
}

const PLAN_COLORS: Record<string, string> = {
  Enterprise: '#3B82F6',
  Professional: '#8B5CF6',
  Pro: '#8B5CF6',
  Starter: '#F59E0B',
  Basic: '#10B981',
  Growth: '#EC4899',
  Team: '#06B6D4',
  Monthly: '#EF4444',
  Annual: '#F97316',
}

export function ContractBreakdownPie({ data }: { data: ContractData[] }) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm shadow-2xl">
          <p className="text-slate-300 font-medium mb-1">{item.plan}</p>
          <p className="text-white font-mono">{item.count} customers</p>
          <p className="text-red-400 font-mono text-xs mt-1">Churn: {(item.churn_rate * 100).toFixed(1)}%</p>
        </div>
      )
    }
    return null
  }

  const renderLegend = (props: any) => {
    const { payload } = props
    return (
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: entry.color }} />
            {entry.value}
          </div>
        ))}
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={60}
          outerRadius={95}
          paddingAngle={3}
          dataKey="count"
          nameKey="plan"
          stroke="none"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={PLAN_COLORS[entry.plan] || '#64748B'} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend content={renderLegend} />
      </PieChart>
    </ResponsiveContainer>
  )
}
