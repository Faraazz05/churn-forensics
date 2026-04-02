import { ConfidenceLevel } from '../../types/api'
import { ConfidenceBadge } from '../../components/ui/ConfidenceBadge'

export function XAIConfidenceBar({ data }: { data: any }) {
  return (
    <div className="bg-[#141E35] border border-[#1E2A45] rounded-xl p-8 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-10">
       <div className="flex-1">
         <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-3">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            Confidence Consensus Rules
         </h3>
         <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
           Our system evaluates the outputs from all 3 selected XAI methods for every single customer prediction. True feature attributions must pass our rigid multi-validator threshold.
         </p>
       </div>
       <div className="flex-shrink-0 grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div className="bg-[#0A0D1A] p-5 border border-[#1E2A45] rounded-lg text-center shadow-inner">
             <div className="mb-3 flex justify-center"><ConfidenceBadge level="HIGH" /></div>
             <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">All 3 Agree</p>
          </div>
          <div className="bg-[#0A0D1A] p-5 border border-[#1E2A45] rounded-lg text-center shadow-inner">
             <div className="mb-3 flex justify-center"><ConfidenceBadge level="MEDIUM" /></div>
             <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">2 Agree</p>
          </div>
          <div className="bg-[#0A0D1A] p-5 border border-red-900/30 bg-red-950/10 rounded-lg text-center shadow-inner">
             <div className="mb-3 flex justify-center"><ConfidenceBadge level="LOW" /></div>
             <p className="text-xs text-red-500/80 font-medium uppercase tracking-wider">Disagreement</p>
          </div>
       </div>
    </div>
  )
}
