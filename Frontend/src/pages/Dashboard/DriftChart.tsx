import { useState } from 'react'
import { PSIBarChart } from '../../components/charts/PSIBarChart'
import { useDriftReport } from '../../hooks/useDrift'
import { AlertTriangle, ChevronRight, X, Sparkles, FileText } from 'lucide-react'

export function DriftChart() {
  const { data: driftData } = useDriftReport()
  const [isExpanded, setIsExpanded] = useState(false)

  const chartData = driftData?.drift_features
    ? driftData.drift_features.slice(0, 5).map(f => ({
        feature: f.feature,
        psi: f.psi ?? 0,
        severity: f.drift_severity || (f.psi && f.psi > 0.2 ? 'Critical' : f.psi && f.psi > 0.1 ? 'Warning' : 'Safe')
      }))
    : []

  const modal = isExpanded ? (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-[#0A0D1A]/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-6xl h-auto max-h-[90vh] flex flex-col p-8 rounded-3xl relative shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/20 transition-all">
         <button onClick={(e) => { e.stopPropagation(); setIsExpanded(false) }} className="absolute z-10 top-6 right-6 p-2.5 bg-white/5 hover:bg-white/10 rounded-full text-white transition-all border border-white/10">
           <X className="w-5 h-5" />
         </button>
         <div className="mb-6 pb-6 border-b border-white/10 pr-12">
           <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3"><AlertTriangle className="w-8 h-8 text-yellow-500"/> Feature Drift Global Report</h2>
           <p className="text-slate-400 text-lg">Deep dive into Population Stability Index (PSI) degradation signals across all tracked data dimensions.</p>
         </div>
         
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8 overflow-y-auto pr-2 custom-scrollbar pb-4">
            <div className="col-span-2 flex flex-col">
               <div className="glass-card flex-1 p-6 flex flex-col min-h-[400px]">
                 <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">Interactive Signal Visualization</h3>
                 <div className="flex-1">
                   <PSIBarChart data={chartData} />
                 </div>
               </div>
            </div>
            
            <div className="col-span-1 flex flex-col gap-6">
               <div className="glass-panel p-8 rounded-2xl border-blue-500/30 bg-blue-500/10 shadow-[0_0_20px_rgba(59,130,246,0.15)] relative overflow-hidden">
                 <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                 <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-blue-300"/> Data Driven Insights</h3>
                 <div className="text-slate-200 text-sm leading-relaxed mb-6 space-y-4 relative z-10">
                   {driftData?.early_warnings && driftData.early_warnings.length > 0 ? (
                     <p>Feature <span className="text-yellow-400 font-mono">{driftData.early_warnings[0].feature}</span> has breached critical degradation thresholds (PSI: {driftData.early_warnings[0].psi}).</p>
                   ) : (
                     <p>No critical early warnings detected in feature distributions.</p>
                   )}
                   <p>System overall drift severity is currently rated as <span className="font-bold text-blue-300">{driftData?.overall_severity || 'Unknown'}</span>.</p>
                 </div>
                 <div className="bg-black/30 border border-white/10 p-4 rounded-xl relative z-10">
                   <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-2 block">Trigger Status</span>
                   <p className="text-sm text-white font-medium">{driftData?.retraining_trigger?.model_retraining_required ? 'Retraining strategy is actively recommended based on PSI indicators.' : 'Model retraining is not required at this time.'}</p>
                 </div>
               </div>
               
               <div className="glass-card p-6 rounded-2xl">
                 <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><FileText className="w-5 h-5 text-slate-400"/> Operational Actions</h3>
                 <button className="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all border border-white/10 flex justify-between items-center px-4 group">
                    <span>Export Full Report (PDF)</span>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                 </button>
                 <button className={`w-full mt-3 py-3 font-medium rounded-xl transition-all border flex justify-between items-center px-4 group ${driftData?.retraining_trigger?.model_retraining_required ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/20' : 'bg-white/5 hover:bg-white/10 text-slate-400 border-white/10'}`}>
                    <span>{driftData?.retraining_trigger?.model_retraining_required ? 'Trigger MLOps Retraining' : 'Retraining Not Queued'}</span>
                    <ChevronRight className={`w-4 h-4 transition-colors ${driftData?.retraining_trigger?.model_retraining_required ? 'text-red-500/50 group-hover:text-red-400' : 'text-slate-600'}`} />
                 </button>
               </div>
            </div>
         </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      {modal}
      <div className="glass-card p-8 relative cursor-pointer group flex flex-col min-h-[400px]" onClick={() => setIsExpanded(true)}>
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
    </>
  )
}
