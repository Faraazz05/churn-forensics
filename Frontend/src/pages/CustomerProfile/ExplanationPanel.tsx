import { ExplanationOut } from '../../types/api'
import { AlertTriangle, LightbulbIcon, CheckCircle2 } from 'lucide-react'

export function ExplanationPanel({ explanation }: { explanation?: ExplanationOut | null }) {
  if (!explanation) return null;

  const reasoning = explanation.reasoning as any;

  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl relative overflow-hidden transition-all hover:border-[#1E2A45]/80">
      <div className="absolute top-0 left-0 w-40 h-40 bg-purple-500/5 rounded-full blur-3xl -ml-10 -mt-10 pointer-events-none" />
      
      <div className="flex items-center gap-4 mb-6 pb-4 border-b border-[#1E2A45]">
         <div className="p-2.5 bg-purple-500/20 shadow-inner rounded-xl border border-purple-500/30">
           <LightbulbIcon className="w-5 h-5 text-purple-400" />
         </div>
         <div>
           <h2 className="text-xl font-bold text-white tracking-wide">AI Reasoning Context</h2>
           <p className="text-slate-400 text-sm">Explaining the prediction logic</p>
         </div>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Model Validation</h3>
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] hover:bg-[#1E2A45]/50 transition-colors">
                <p className="text-slate-400 text-xs mb-1 font-medium">Methodology</p>
                <p className="text-white font-bold">{explanation.primary_method}</p>
             </div>
             <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] hover:bg-[#1E2A45]/50 transition-colors">
                <p className="text-slate-400 text-xs mb-1 font-medium">Validators Active</p>
                <p className="text-emerald-400 font-bold flex items-center gap-1">
                   <CheckCircle2 className="w-4 h-4" /> {explanation.validators_active}
                </p>
             </div>
          </div>
        </div>

        {reasoning?.what_changed && (
          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              What Changed Recently
            </h3>
            <div className="space-y-3">
              {(reasoning.what_changed as string[]).slice(0, 3).map((change, i) => (
                 <div key={i} className="px-4 py-3 bg-orange-500/5 border border-orange-500/20 rounded-lg text-sm text-slate-300 flex items-start gap-3 relative overflow-hidden">
                   <div className="absolute left-0 top-0 bottom-0 w-1 bg-orange-500/50" />
                   <span className="leading-relaxed">{change}</span>
                 </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
