import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

export function ChurnProbabilityGauge({ probability }: { probability: number }) {
  const data = [
    { name: 'Risk', value: probability },
    { name: 'Safe', value: 1 - probability }
  ]
  
  const getColor = (p: number) => {
    if (p >= 0.7) return '#EF4444'
    if (p >= 0.4) return '#F59E0B'
    return '#10B981'
  }

  return (
    <div className="relative w-full h-[200px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="70%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            paddingAngle={0}
            dataKey="value"
            stroke="none"
          >
            <Cell key="risk" fill={getColor(probability)} />
            <Cell key="safe" fill="#1E2A45" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-8 pointer-events-none">
        <span className="text-3xl font-bold font-mono text-slate-100">
          {(probability * 100).toFixed(1)}%
        </span>
        <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Churn Risk</span>
      </div>
    </div>
  )
}
