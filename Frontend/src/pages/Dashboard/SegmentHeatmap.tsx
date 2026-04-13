import { SegmentHeatmapChart } from '../../components/charts/SegmentHeatmapChart'
import { useSegments } from '../../hooks/useSegments'
import { ChevronRight, Download } from 'lucide-react'

export function SegmentHeatmap() {
  const { data } = useSegments()
  
  const chartData = data?.segments && data.segments.length > 0
    ? data.segments.slice(0, 10).map((s) => ({ x: s.value, y: s.dimension, value: s.churn_rate || 0 }))
    : []

  return (
    <div className="glass-card p-8 h-full relative group flex flex-col">
      <div className="absolute inset-0 bg-blue-500/[0.04] opacity-0 group-hover:opacity-100 transition duration-500 rounded-xl pointer-events-none" />
      
      <div className="flex items-start justify-between mb-8 border-b border-white/10 pb-4 relative z-10">
        <div>
           <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
             Segment Risk Heatmap
           </h2>
           <p className="text-sm text-slate-400 mt-1">Churn vulnerability mapped by Region × Plan</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:text-white group-hover:bg-blue-600 transition-all border border-white/10 shadow-sm relative z-10 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.6)] group-hover:scale-110 cursor-pointer pointer-events-auto" onClick={() => console.log("Exporting Segment Heatmap...")}>
             <Download className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" />
          </button>
          <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:text-white group-hover:bg-blue-600 transition-all border border-white/10 shadow-sm relative z-10 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.6)] group-hover:scale-110">
             <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </div>
        </div>
      </div>
      
      <div className="flex-1 w-full h-full flex items-center justify-center relative z-10 pointer-events-none -ml-4">
         {chartData.length > 0 ? <SegmentHeatmapChart data={chartData} /> : <div className="text-slate-500 text-sm ml-4">No segment data available to map.</div>}
      </div>
    </div>
  )
}
