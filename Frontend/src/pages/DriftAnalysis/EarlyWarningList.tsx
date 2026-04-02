import { DriftFeatureOut } from '../../types/api'
import { AlertCircle, Activity, CheckCircle } from 'lucide-react'

export function EarlyWarningList({ predrifts }: { predrifts?: DriftFeatureOut[] }) {
  const list = predrifts || []
  
  if (list.length === 0) {
     return (
       <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl text-center h-full flex flex-col items-center justify-center min-h-[400px]">
          <div className="p-4 bg-emerald-500/10 rounded-full mb-4">
             <CheckCircle className="w-12 h-12 text-emerald-500" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">No Early Warnings</h3>
          <p className="text-slate-500 max-w-sm">All model features are currently stable and tracking well within acceptable drift thresholds.</p>
       </div>
     )
  }

  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 border-b border-[#1E2A45] pb-4">
         <h2 className="text-xl font-bold text-white flex items-center gap-3">
           <div className="p-2 bg-orange-500/20 rounded-lg">
             <Activity className="w-5 h-5 text-orange-400" />
           </div>
           Early Warning Signals
         </h2>
         <span className="text-xs font-bold bg-orange-500/10 text-orange-400 px-3 py-1.5 rounded border border-orange-500/20 shadow-inner">
            {list.length} DETECTED
         </span>
      </div>
      
      <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1">
        {list.map((f, i) => (
          <div key={i} className="bg-[#141E35] p-5 rounded-xl border border-[#1E2A45] hover:border-orange-500/30 transition-all group relative overflow-hidden">
             
             <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-3">
                <span className="text-white font-medium">{f.feature}</span>
                <span className="text-xs bg-red-500/10 text-red-400 px-2.5 py-1 rounded font-bold shadow-inner border border-red-500/20 font-mono">
                   PSI: {f.psi?.toFixed(3)}
                </span>
             </div>
             
             <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0A0D1A] p-3 rounded-lg border border-[#1E2A45]">
                   <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Velocity</p>
                   <p className="text-sm text-slate-300 font-medium">{f.velocity || 'N/A'}</p>
                </div>
                <div className="bg-[#0A0D1A] p-3 rounded-lg border border-[#1E2A45]">
                   <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Trend</p>
                   <p className="text-sm text-slate-300 font-medium">{f.trend || 'N/A'}</p>
                </div>
             </div>
             
             {f.xai_confirmed && (
               <div className="mt-4 pt-3 flex items-center gap-2 text-xs text-orange-400 font-medium">
                  <AlertCircle className="w-4 h-4" /> Feature affects high-risk predictions
               </div>
             )}
          </div>
        ))}
      </div>
    </div>
  )
}
