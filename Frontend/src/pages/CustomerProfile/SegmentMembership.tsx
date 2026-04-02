import { SegmentOut } from '../../types/api'
import { Users, TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'

export function SegmentMembership({ segment }: { segment?: SegmentOut | null }) {
  if (!segment) return null;

  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl relative overflow-hidden group hover:border-[#1E2A45]/80 transition-all">
       <div className="flex items-center justify-between mb-6 border-b border-[#1E2A45] pb-4">
          <div className="flex items-center gap-3">
             <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
               <Users className="w-5 h-5" />
             </div>
             <h2 className="text-xl font-bold text-white">Segment Context</h2>
          </div>
          {segment.health_status === 'degrading' ? (
             <span className="flex items-center gap-1.5 px-3 py-1 bg-red-500/10 text-red-500 text-xs font-bold rounded-lg border border-red-500/20">
               <TrendingDown className="w-3.5 h-3.5" /> DEGRADING
             </span>
          ) : segment.health_status === 'improving' ? (
             <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-500 text-xs font-bold rounded-lg border border-emerald-500/20">
               <TrendingUp className="w-3.5 h-3.5" /> IMPROVING
             </span>
          ) : (
             <span className="flex items-center gap-1.5 px-3 py-1 bg-slate-500/10 text-slate-400 text-xs font-bold rounded-lg border border-slate-500/20">
               <Minus className="w-3.5 h-3.5" /> STABLE
             </span>
          )}
       </div>

       <div className="mb-6">
         <p className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-bold">Identified Cohort</p>
         <h3 className="text-2xl font-bold text-white">{segment.segment_id}</h3>
       </div>

       <div className="grid grid-cols-2 gap-4">
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45]">
            <p className="text-slate-400 text-xs mb-2 flex items-center gap-2">
              <Activity className="w-3.5 h-3.5" /> Cohort Churn Rate
            </p>
            <p className="text-white font-bold text-lg">
               {segment.churn_rate ? (segment.churn_rate * 100).toFixed(1) + '%' : 'N/A'}
            </p>
         </div>
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45]">
            <p className="text-slate-400 text-xs mb-2">Revenue at Risk</p>
            <p className="text-white font-bold text-lg text-emerald-400">
               {segment.revenue_at_risk ? `$${(segment.revenue_at_risk / 1000).toFixed(1)}k` : 'N/A'}
            </p>
         </div>
       </div>

       {segment.exceeds_benchmark && (
         <div className="mt-4 p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-sm text-red-200 text-center">
            Critical: Exceeds standard industry churn benchmarks.
         </div>
       )}
    </div>
  )
}
