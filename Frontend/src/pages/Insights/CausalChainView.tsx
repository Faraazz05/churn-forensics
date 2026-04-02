import { ArrowRight, Link as LinkIcon, Network } from 'lucide-react'

export function CausalChainView({ data }: { data?: any }) {
  if (!data?.causal_chains || data.causal_chains.length === 0) return null;

  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
      <div className="flex items-center gap-3 mb-8 border-b border-[#1E2A45] pb-4">
         <div className="p-2.5 bg-purple-500/20 rounded-xl shadow-inner border border-purple-500/30">
           <Network className="w-5 h-5 text-purple-400" />
         </div>
         <div>
           <h2 className="text-xl font-bold text-white tracking-wide">Causal Reasoning Chain</h2>
           <p className="text-slate-400 text-sm">Identifying root causes via SHAP impact</p>
         </div>
      </div>

      <div className="space-y-8 relative">
         <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-gradient-to-b from-purple-500/50 to-purple-500/5 z-0"></div>
         
         {data.causal_chains.map((chain: any, i: number) => (
            <div key={i} className="pl-14 relative z-10 transition-transform hover:translate-x-2">
               <div className="absolute left-4 top-1/2 -mt-2 w-4 h-4 rounded-full bg-[#0F1629] border-2 border-purple-500 flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.5)]">
                 <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
               </div>
               <div className="bg-[#141E35] p-5 rounded-xl border border-[#1E2A45] hover:border-purple-500/40 transition-colors shadow-lg">
                  <div className="flex justify-between items-center mb-4">
                     <span className="text-slate-400 text-xs font-mono tracking-wider font-bold">CUSTOMER {chain.customer_id}</span>
                     <LinkIcon className="w-4 h-4 text-purple-500/50" />
                  </div>
                  <div className="flex flex-col gap-3">
                     <div className="p-3 bg-[#0A0D1A] rounded-lg border border-[#1E2A45] shadow-inner">
                        <p className="text-xs text-slate-500 mb-1 font-bold uppercase tracking-wider">Primary Driver</p>
                        <p className="text-white font-medium">{chain.primary || 'N/A'}</p>
                     </div>
                     <div className="flex justify-center -my-4 z-10">
                        <div className="bg-[#1E2A45] rounded-full p-1.5 border border-purple-500/30">
                           <ArrowRight className="w-4 h-4 text-purple-400" />
                        </div>
                     </div>
                     <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20 shadow-inner">
                        <p className="text-xs text-purple-400/80 mb-1 font-bold uppercase tracking-wider">Root Cause Inference</p>
                        <p className="text-purple-100 font-medium">{chain.mechanism || 'N/A'}</p>
                     </div>
                  </div>
               </div>
            </div>
         ))}
      </div>
    </div>
  )
}
