import { DollarSign, ShieldAlert, Target } from 'lucide-react'

export function BusinessImpactPanel({ impact }: { impact?: any }) {
  if (!impact) return null;

  return (
    <div className="bg-gradient-to-br from-[#1E2A45] to-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl relative overflow-hidden group hover:border-[#1E2A45]/80 transition-all">
       <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#1E2A45] relative z-10">
         <div className="p-2.5 bg-emerald-500/20 rounded-xl shadow-inner border border-emerald-500/30">
           <DollarSign className="w-5 h-5 text-emerald-400" />
         </div>
         <div>
           <h2 className="text-xl font-bold text-white tracking-wide">Business Impact</h2>
           <p className="text-slate-400 text-sm">Financial projections & recovery targets</p>
         </div>
       </div>

       <div className="grid grid-cols-2 gap-4 mb-6 relative z-10">
          <div className="bg-[#141E35]/80 backdrop-blur-sm p-5 rounded-xl border border-red-500/20 relative overflow-hidden shadow-inner">
             <div className="absolute top-0 right-0 p-2 opacity-5 -mt-2 -mr-2"><ShieldAlert className="w-16 h-16 text-red-500"/></div>
             <p className="text-slate-400 text-xs mb-2 uppercase tracking-widest font-bold">Projected Loss (No Action)</p>
             <p className="text-3xl font-bold text-red-400 drop-shadow-[0_0_10px_rgba(248,113,113,0.3)]">
               ${((impact.projected_loss_if_no_action || 0)/1000).toFixed(1)}k
             </p>
          </div>
          <div className="bg-[#141E35]/80 backdrop-blur-sm p-5 rounded-xl border border-emerald-500/20 relative overflow-hidden shadow-inner">
             <div className="absolute top-0 right-0 p-2 opacity-5 -mt-2 -mr-2"><Target className="w-16 h-16 text-emerald-500"/></div>
             <p className="text-slate-400 text-xs mb-2 uppercase tracking-widest font-bold">Potential Recovery</p>
             <p className="text-3xl font-bold text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.3)]">
               ${((impact.potential_recovery || 0)/1000).toFixed(1)}k
             </p>
          </div>
       </div>

       <div className="space-y-3 relative z-10">
          <div className="flex justify-between items-center p-3.5 bg-[#0A0D1A] rounded-lg border border-[#1E2A45] hover:bg-[#1E2A45]/50 transition-colors">
             <span className="text-slate-400 text-sm font-medium">Critical Customers</span>
             <span className="text-white font-mono font-bold bg-slate-800 px-2 py-0.5 rounded shadow-inner">{impact.critical_customers_count || 0}</span>
          </div>
          <div className="flex justify-between items-center p-3.5 bg-[#0A0D1A] rounded-lg border border-[#1E2A45] hover:bg-[#1E2A45]/50 transition-colors">
             <span className="text-slate-400 text-sm font-medium">High Risk Customers</span>
             <span className="text-white font-mono font-bold bg-slate-800 px-2 py-0.5 rounded shadow-inner">{impact.high_risk_customers_count || 0}</span>
          </div>
          <div className="flex justify-between items-center p-3.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20 shadow-inner">
             <span className="text-emerald-400/80 text-sm font-medium">Recovery Assumption</span>
             <span className="text-emerald-400 text-sm font-bold tracking-wide">{impact.recovery_assumption || 'Standard'}</span>
          </div>
       </div>
    </div>
  )
}
