import { Zap, ArrowRight, Activity, Calendar } from 'lucide-react'

export function ActionCard({ customerId, insights }: { customerId: string, insights?: any }) {
  // Use RL or LLM insights if available, fallback otherwise
  
  return (
    <div className="bg-gradient-to-br from-[#1E2A45] to-[#0F1629] p-8 rounded-xl border border-blue-500/30 shadow-[0_0_30px_rgba(59,130,246,0.1)] relative overflow-hidden">
       <div className="absolute right-0 top-0 text-blue-500/5 transform translate-x-1/4 -translate-y-1/4 pointer-events-none">
          <Zap className="w-64 h-64" />
       </div>
       
       <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-blue-500 text-white rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.5)]">
             <Zap className="w-5 h-5 fill-current" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-wide">Recommended Next Action</h2>
            <p className="text-blue-300/70 text-sm">AI-Generated Intervention Strategy</p>
          </div>
       </div>

       <div className="bg-[#0A0D1A]/50 p-6 rounded-xl border border-blue-500/20 backdrop-blur-sm mb-6">
          <h3 className="text-white text-lg font-medium leading-relaxed mb-4">
            {insights?.top_action || "Schedule immediate executive alignment meeting to review Q2 roadmaps and address outstanding severity-1 tickets."}
          </h3>
          
          <div className="flex flex-wrap gap-3">
             <span className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs font-bold text-blue-300 flex items-center gap-1.5">
               <Activity className="w-3.5 h-3.5" /> High Impact (+12% Retention)
             </span>
             <span className="px-3 py-1.5 bg-slate-500/10 border border-slate-500/20 rounded-lg text-xs font-bold text-slate-300 flex items-center gap-1.5">
               <Calendar className="w-3.5 h-3.5" /> Action within 48h
             </span>
          </div>
       </div>

       <div className="flex justify-end">
          <button className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all shadow-[0_0_20px_rgba(59,130,246,0.4)] hover:shadow-[0_0_25px_rgba(59,130,246,0.6)]">
             Execute Playbook <ArrowRight className="w-4 h-4" />
          </button>
       </div>
    </div>
  )
}
