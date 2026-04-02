import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { FeatureExplanation } from '../../types/api'

export function FeatureImportanceBar({ data }: { data: FeatureExplanation[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1E2A45" horizontal={false} />
        <XAxis type="number" dataKey="importance" stroke="#64748B" />
        <YAxis dataKey="feature" type="category" stroke="#64748B" tick={{ fontSize: 12 }} width={120} />
        <Tooltip 
          cursor={{ fill: '#141E35' }}
          contentStyle={{ backgroundColor: '#0F1629', borderColor: '#1E2A45', color: '#F1F5F9', borderRadius: '8px' }} 
        />
        <Bar dataKey="importance" radius={[0, 4, 4, 0]} maxBarSize={30}>
          {data.map((entry, index) => (
             <Cell key={`cell-${index}`} fill={entry.direction === 'risk+' ? '#EF4444' : '#10B981'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
