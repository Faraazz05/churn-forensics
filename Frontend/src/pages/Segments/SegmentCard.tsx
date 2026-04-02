import { SegmentOut } from '../../types/api'
import { DegradationBadge } from './DegradationBadge'
import { AlertCircle } from 'lucide-react'

export function SegmentCard({ segment }: { segment: SegmentOut }) {
  return (
    <div className="bg-[#0F1629] p-6 rounded-xl border border-[#1E2A45] shadow-lg hover:border-blue-500/30 transition-all group relative overflow-hidden">
      <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
      
      <div className="flex justify-between items-start mb-5">
        <div>
          <h3 className="text-white font-bold text-lg leading-tight">{segment.segment_id}</h3>
          <div className="mt-2">
             <span className="px-2 py-1 bg-[#141E35] border border-[#1E2A45] rounded-md font-mono text-xs text-blue-300">
               {segment.dimension} = {segment.value}
             </span>
          </div>
        </div>
        <DegradationBadge status={segment.health_status} delta={segment.churn_delta} />
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-2">
         <div className="bg-[#141E35] p-3 rounded-lg border border-[#1E2A45]">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1 font-bold">Churn Rate</p>
            <p className="text-xl font-bold text-white">{(segment.churn_rate ? segment.churn_rate * 100 : 0).toFixed(1)}%</p>
         </div>
         <div className="bg-[#141E35] p-3 rounded-lg border border-[#1E2A45]">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1 font-bold">Rev at Risk</p>
            <p className="text-xl font-bold text-red-400">${((segment.revenue_at_risk || 0)/1000).toFixed(1)}k</p>
         </div>
      </div>
      
      {segment.exceeds_benchmark && (
         <div className="mt-4 pt-3 border-t border-[#1E2A45] flex items-center gap-2 text-xs font-bold text-orange-400">
           <AlertCircle className="w-4 h-4" /> EXCEEDS INDUSTRY BENCHMARK
         </div>
      )}
    </div>
  )
}
