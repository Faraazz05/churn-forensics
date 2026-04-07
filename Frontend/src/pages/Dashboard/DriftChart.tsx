import { PSIBarChart } from '../../components/charts/PSIBarChart'
import { useDriftReport } from '../../hooks/useDrift'
import { AlertTriangle, ChevronRight } from 'lucide-react'

export function DriftChart() {
  const { data: driftData } = useDriftReport()

  const chartData = driftData?.drift_features
    ? driftData.drift_features.slice(0, 5).map(f => ({
        feature: f.feature,
        psi: f.psi ?? 0,
        severity: f.drift_severity || (f.psi && f.psi > 0.2 ? 'Critical' : f.psi && f.psi > 0.1 ? 'Warning' : 'Safe')
      }))
    : []

  return (
    <div className="glass-card p-8 relative group flex flex-col min-h-[400px]">
      <div className="absolute inset-0 bg-blue-500/[0.04] opacity-0 group-hover:opacity-100 transition duration-500 rounded-xl pointer-events-none" />
      
      <div className="flex items-start justify-between mb-8 border-b border-white/10 pb-4 relative z-10">
        <div>
           <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
             <AlertTriangle className="w-5 h-5 text-yellow-400 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]" /> Feature Drift Alerts
           </h2>
           <p className="text-sm text-slate-400 mt-1">Population Stability Index tracking over trailing 30d</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:text-white group-hover:bg-blue-600 transition-all border border-white/10 shadow-sm relative z-10 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.6)] group-hover:scale-110">
           <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </div>
      
      <div className="flex-1 w-full relative z-10 pointer-events-none">
         {chartData.length > 0 ? <PSIBarChart data={chartData} /> : <div className="h-full flex items-center justify-center text-slate-500 text-sm">No drift feature data available.</div>}
      </div>
    </div>
  )
}
