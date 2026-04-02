import { FeatureExplanation } from '../../types/api'

export function FeatureImportanceChart({ explanations }: { explanations?: FeatureExplanation[] | null }) {
  const data = explanations || [];
  
  if (data.length === 0) return null;

  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl">
      <h2 className="text-xl font-bold text-white mb-6 border-b border-[#1E2A45] pb-4">Primary Feature Drivers</h2>
      <div className="space-y-4">
         {data.map((exp, i) => (
           <div key={i} className="bg-[#141E35] p-5 rounded-xl border border-[#1E2A45] transition hover:bg-[#1E2A45]/50 group relative overflow-hidden">
             
             <div className="flex justify-between items-center mb-3">
               <span className="text-slate-200 font-medium group-hover:text-white transition-colors flex items-center gap-2">
                 <span className="text-slate-500 text-sm font-mono opacity-50">#{(i+1).toString().padStart(2, '0')}</span>
                 {exp.feature}
               </span>
               <span className={`text-xs font-bold px-2 py-0.5 rounded shadow-inner ${
                 exp.direction === 'risk+' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
               }`}>
                 {exp.direction === 'risk+' ? '↑ Drives Risk' : '↓ Lowers Risk'}
               </span>
             </div>
             
             <div className="h-2.5 w-full bg-[#0A0D1A] rounded-full overflow-hidden flex shadow-inner border border-white/5">
               <div 
                 className={`h-full transition-all duration-1000 ${
                   exp.direction === 'risk+' 
                     ? 'bg-gradient-to-r from-red-600 to-red-400 shadow-[0_0_10px_rgba(239,68,68,0.5)]' 
                     : 'bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                 }`}
                 style={{ width: `${Math.max(2, Math.min(100, exp.importance * 100))}%` }}
               />
             </div>
             <p className="text-right text-xs text-slate-500 mt-2 font-mono group-hover:text-slate-400 transition-colors">
               MAGNITUDE: {(exp.importance).toFixed(3)}
             </p>
           </div>
         ))}
      </div>
    </div>
  )
}
