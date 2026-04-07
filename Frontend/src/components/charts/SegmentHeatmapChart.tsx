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
        <div className="bg-[#0F1629] border border-[#1E2A45] px-4 py-3 rounded-xl text-sm text-slate-200 shadow-2xl">
          <p className="font-medium text-slate-300 mb-1">{`${data.y} × ${data.x}`}</p>
          <p className="font-bold text-blue-400 text-base">{`Churn: ${(data.value * 100).toFixed(1)}%`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ScatterChart margin={{ top: 24, right: 30, bottom: 30, left: 80 }}>
        <XAxis
          type="category"
          dataKey="x"
          name="Category X"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 13, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          dy={10}
        />
        <YAxis
          type="category"
          dataKey="y"
          name="Category Y"
          stroke="#475569"
          tick={{ fill: '#94A3B8', fontSize: 13, fontWeight: 500 }}
          tickLine={{ stroke: '#334155' }}
          axisLine={{ stroke: '#1E2A45' }}
          dx={-8}
        />
        <ZAxis type="number" dataKey="value" range={[500, 500]} />
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
