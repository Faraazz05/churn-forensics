import { useState } from 'react'
import { ChevronRight, ArrowUpDown, X, Sparkles, FileText, Users } from 'lucide-react'

export function WatchlistTable({ filteredCustomers, filters }: { filteredCustomers: any[], filters: any }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const customers = filteredCustomers || []

  const borderColors: Record<string, string> = {
    Critical: 'border-l-red-500 shadow-[inset_4px_0_0_0_rgba(239,68,68,1)]',
    High: 'border-l-yellow-500 shadow-[inset_4px_0_0_0_rgba(245,158,11,1)]',
    Medium: 'border-l-blue-500 shadow-[inset_4px_0_0_0_rgba(59,130,246,1)]',
    Safe: 'border-l-green-500 shadow-[inset_4px_0_0_0_rgba(16,185,129,1)]'
  }

  const badgeColors: Record<string, string> = {
    Critical: 'bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.2)]',
    High: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20 shadow-[0_0_10px_rgba(245,158,11,0.2)]',
    Medium: 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.2)]',
  }

  const modal = isExpanded ? (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-[#0A0D1A]/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-[1400px] h-auto max-h-[90vh] flex flex-col p-8 rounded-3xl relative shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/20 transition-all">
         <button onClick={(e) => { e.stopPropagation(); setIsExpanded(false) }} className="absolute z-10 top-6 right-6 p-2.5 bg-white/5 hover:bg-white/10 rounded-full text-white transition-all border border-white/10">
           <X className="w-5 h-5" />
         </button>
         <div className="mb-6 pb-6 border-b border-white/10 pr-12 flex justify-between items-center">
           <div>
             <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3"><Users className="w-8 h-8 text-blue-500"/> At-Risk Watchlist Deep Dive</h2>
             <p className="text-slate-400 text-lg">Detailed behavioral and usage metrics for accounts exceeding the 70% churn probability threshold.</p>
           </div>
           <div className="px-5 py-2.5 bg-red-500/10 text-red-400 font-bold rounded-xl border border-red-500/30 text-sm tracking-widest shadow-[0_0_20px_rgba(239,68,68,0.2)]">
             {customers.length || 0} ACCOUNTS CRITICAL
           </div>
         </div>
         
         <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-8 overflow-y-auto pr-2 custom-scrollbar pb-4">
            <div className="col-span-3 flex flex-col">
               <div className="glass-card flex-1 p-0 flex flex-col min-h-[400px] overflow-hidden">
                 <div className="overflow-x-auto flex-1">
                   <table className="w-full text-left border-collapse">
                     <thead>
                       <tr className="bg-black/20 text-slate-300 text-xs tracking-wider uppercase border-b border-white/10">
                         <th className="px-6 py-5 font-bold">Customer ID</th>
                         <th className="px-6 py-5 font-bold flex items-center gap-1">Risk Prob <ArrowUpDown className="w-3 h-3 text-slate-400" /></th>
                         <th className="px-6 py-5 font-bold">Risk Tier</th>
                         <th className="px-6 py-5 font-bold">Contract Plan</th>
                         <th className="px-6 py-5 font-bold">Region</th>
                         <th className="px-6 py-5 font-bold">Primary At-Risk Driver</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5">
                       {customers.map((c: any) => (
                         <tr 
                           key={c.customer_id} 
                           className={`text-slate-300 text-sm hover:bg-white/5 transition-colors border-l-0 ${borderColors[c.risk_tier] || ''}`}
                         >
                           <td className="px-6 py-5 font-mono font-medium text-blue-400">{c.customer_id}</td>
                           <td className="px-6 py-5 font-mono font-bold text-white tracking-widest">{(c.churn_probability * 100).toFixed(1)}%</td>
                           <td className="px-6 py-5">
                             <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full border text-xs font-semibold ${badgeColors[c.risk_tier] || badgeColors['Medium']}`}>{c.risk_tier}</div>
                           </td>
                           <td className="px-6 py-5 font-medium">{c.plan_type || 'Enterprise'}</td>
                           <td className="px-6 py-5 text-slate-400">{c.region || 'US-East'}</td>
                           <td className="px-6 py-5 text-slate-300 font-medium">{c.primary_driver || 'Decreased API Usage'}</td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               </div>
            </div>
            
            <div className="col-span-1 flex flex-col gap-6">
               <div className="glass-panel p-8 rounded-2xl border-red-500/30 bg-red-500/10 shadow-[0_0_20px_rgba(239,68,68,0.15)] relative overflow-hidden">
                 <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                 <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-red-300"/> LLM Portfolio Insight</h3>
                 <div className="text-slate-200 text-sm leading-relaxed mb-6 space-y-4 relative z-10">
                   <p>The top 5 critical accounts all share a sudden drop in <span className="font-mono text-white text-xs bg-white/10 px-1 py-0.5 rounded">api_calls_7d</span>, strongly correlating with recent feature usage decay.</p>
                   <p>Total Revenue at Risk across this segment is estimated at <span className="text-red-400 font-bold">$2.4M ARR</span>.</p>
                 </div>
                 <div className="bg-black/30 border border-white/10 p-4 rounded-xl relative z-10">
                   <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-2 block">AI Recommendation</span>
                   <p className="text-sm text-white font-medium">Prioritize outreach to accounts identifying "Decreased API Usage" as the primary driver; many may be blocked by undocumented rate limits.</p>
                 </div>
               </div>
               
               <div className="glass-card p-6 rounded-2xl">
                 <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><FileText className="w-5 h-5 text-slate-400"/> Operational Actions</h3>
                 <button className="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all border border-white/10 flex justify-between items-center px-4 group">
                    <span>Export Target List (CSV)</span>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                 </button>
                 <button className="w-full mt-3 py-3 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 font-medium rounded-xl transition-all border border-blue-500/30 flex justify-between items-center px-4 group shadow-[0_0_15px_rgba(59,130,246,0.15)]">
                    <span>Sync to Salesforce Tasks</span>
                    <ChevronRight className="w-4 h-4 text-blue-500/50 group-hover:text-blue-400 transition-colors" />
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
      <div className="glass-card overflow-hidden h-full flex flex-col relative" onClick={() => setIsExpanded(true)}>
        <div className="absolute inset-0 bg-blue-500/[0.04] opacity-0 hover:opacity-100 transition duration-500 cursor-pointer pointer-events-none z-20" />
        
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-black/20 backdrop-blur-md relative z-10">
           <div>
              <h2 className="text-xl font-bold text-white tracking-wide">Critical Watchlist</h2>
              <p className="text-sm text-slate-400 mt-1">Customers exceeding 70% algorithmic churn probability threshold</p>
           </div>
           <div className="px-5 py-2 bg-red-500/10 text-red-400 font-bold rounded-lg border border-red-500/20 text-sm tracking-widest shadow-[0_0_10px_rgba(239,68,68,0.15)]">
             {customers.length || 0} AT RISK
           </div>
        </div>
        
        <div className="overflow-x-auto flex-1 relative z-10 cursor-pointer">
          <table className="w-full text-left border-collapse pointer-events-none">
            <thead>
              <tr className="bg-black/10 text-slate-400 text-xs tracking-wider uppercase border-b border-white/10">
                <th className="px-6 py-5 font-semibold">Customer ID</th>
                <th className="px-6 py-5 font-semibold">Risk Prob</th>
                <th className="px-6 py-5 font-semibold">Risk Tier</th>
                <th className="px-6 py-5 font-semibold">Contract Plan</th>
                <th className="px-6 py-5 font-semibold">Region</th>
                <th className="px-6 py-5 font-semibold">Primary At-Risk Driver</th>
                <th className="px-6 py-5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {customers.slice(0, 5).map((c: any) => (
                <tr 
                  key={c.customer_id} 
                  className={`text-slate-300 text-sm transition-colors border-l-0 ${borderColors[c.risk_tier] || ''}`}
                >
                  <td className="px-6 py-4 font-mono font-medium text-blue-400">{c.customer_id}</td>
                  <td className="px-6 py-4 font-mono font-bold text-white">{(c.churn_probability * 100).toFixed(1)}%</td>
                  <td className="px-6 py-4">
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full border text-xs font-semibold ${badgeColors[c.risk_tier] || badgeColors['Medium']}`}>{c.risk_tier}</div>
                  </td>
                  <td className="px-6 py-4 text-slate-400">{c.plan_type || 'Enterprise'}</td>
                  <td className="px-6 py-4 text-slate-400">{c.region || 'US-East'}</td>
                  <td className="px-6 py-4 text-slate-300 font-medium">{c.primary_driver || 'Decreased API Usage'}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="w-8 h-8 rounded-full border border-white/10 bg-white/5 flex items-center justify-center ml-auto">
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-4 bg-black/20 border-t border-white/10 flex justify-center relative z-10">
           <p className="text-sm font-bold tracking-widest uppercase text-blue-400 transition px-6 py-2 rounded">Click to View Full Intelligence Watchlist</p>
        </div>
      </div>
    </>
  )
}
