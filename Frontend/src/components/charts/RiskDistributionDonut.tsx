import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

export function RiskDistributionDonut({ data }: { data: { name: string; value: number }[] }) {
  const COLORS: Record<string, string> = {
    Critical: '#EF4444',
    High: '#F59E0B',
    Medium: '#3B82F6',
    Safe: '#10B981',
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          stroke="none"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#64748B'} />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{ backgroundColor: '#0F1629', borderColor: '#1E2A45', color: '#F1F5F9', borderRadius: '8px' }} 
          itemStyle={{ color: '#F1F5F9' }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
