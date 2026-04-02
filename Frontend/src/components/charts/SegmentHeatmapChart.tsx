import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, ResponsiveContainer, Cell, Tooltip } from 'recharts'

interface HeatmapData {
  x: string
  y: string
  value: number // churn rate
}

export function SegmentHeatmapChart({ data }: { data: HeatmapData[] }) {
  const parseColor = (val: number) => {
    if (val > 0.3) return '#EF4444'
    if (val > 0.15) return '#F59E0B'
    return '#10B981'
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-[#0F1629] border border-[#1E2A45] p-2 rounded text-sm text-slate-200 shadow-xl">
          <p>{`${data.y} × ${data.x}`}</p>
          <p className="font-bold text-blue-400">{`Churn: ${(data.value * 100).toFixed(1)}%`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 60 }}>
        <XAxis type="category" dataKey="x" name="Category X" stroke="#64748B" tick={{ fill: '#64748B', fontSize: 12 }} />
        <YAxis type="category" dataKey="y" name="Category Y" stroke="#64748B" tick={{ fill: '#64748B', fontSize: 12 }} />
        <ZAxis type="number" dataKey="value" range={[400, 400]} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(30, 42, 69, 0.4)' }} />
        <Scatter data={data} shape="square">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={parseColor(entry.value)} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}
