import { useState } from 'react'
import { SegmentHeatmapChart } from '../../components/charts/SegmentHeatmapChart'
import { useSegments } from '../../hooks/useSegments'
import { BarChart2, ChevronRight, X, Sparkles, FileText } from 'lucide-react'

export function SegmentHeatmap() {
  const { data } = useSegments()
  const [isExpanded, setIsExpanded] = useState(false)
  
  const chartData = data?.segments && data.segments.length > 0
    ? data.segments.slice(0, 10).map((s) => ({ x: s.dimension, y: s.value, value: s.churn_rate || 0 }))
    : []

  const modal = isExpanded ? (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-[#0A0D1A]/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-6xl h-auto max-h-[90vh] flex flex-col p-8 rounded-3xl relative shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/20 transition-all">
         <button onClick={(e) => { e.stopPropagation(); setIsExpanded(false) }} className="absolute z-10 top-6 right-6 p-2.5 bg-white/5 hover:bg-white/10 rounded-full text-white transition-all border border-white/10">
           <X className="w-5 h-5" />
         </button>
         <div className="mb-6 pb-6 border-b border-white/10 pr-12">
           <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3"><BarChart2 className="w-8 h-8 text-blue-500"/> Segment Risk Heatmap</h2>
           <p className="text-slate-400 text-lg">Detailed churn risk density mapping across Region and Subscription Plan dimensions.</p>
         </div>
         
         <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8 overflow-y-auto pr-2 custom-scrollbar pb-4">
            <div className="col-span-2 flex flex-col">
               <div className="glass-card flex-1 p-6 flex flex-col min-h-[400px]">
                 <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">Interactive Signal Visualization</h3>
                 <div className="flex-1 w-full h-full flex items-center justify-center -ml-4">
                   <SegmentHeatmapChart data={chartData} />
                 </div>
               </div>
            </div>
            
            <div className="col-span-1 flex flex-col gap-6">
               <div className="glass-panel p-8 rounded-2xl border-purple-500/30 bg-purple-500/10 shadow-[0_0_20px_rgba(168,85,247,0.15)] relative overflow-hidden">
                 <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                 <h3 className="text-xl font-bold text-purple-400 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-purple-300"/> Dynamic Insight Generation</h3>
                 <div className="text-slate-200 text-sm leading-relaxed mb-6 space-y-4 relative z-10">
                   {data?.segments && data.segments.length > 0 ? (
                     <>
                       <p>The <span className="text-pink-400 font-mono">{data.segments[0].value}</span> segment in <span className="text-pink-400 font-mono">{data.segments[0].dimension}</span> exhibits one of the highest densities of predicted churn risk ({(data.segments[0].churn_rate || 0.0) * 100}%).</p>
                       <p>Health Status: <span className="uppercase tracking-wider font-bold text-slate-300">{data.segments[0].health_status || 'Unknown'}</span></p>
                     </>
                   ) : (
                     <p>No high-risk segments have been detected currently.</p>
                   )}
                 </div>
                 <div className="bg-black/30 border border-white/10 p-4 rounded-xl relative z-10">
                   <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-2 block">System Recommendation</span>
                   <p className="text-sm text-white font-medium">{data?.global_insights?.recommended_strategy || 'Review global segment distributions to identify emerging risk patterns before they accelerate.'}</p>
                 </div>
               </div>
               
               <div className="glass-card p-6 rounded-2xl">
                 <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><FileText className="w-5 h-5 text-slate-400"/> Operational Actions</h3>
                 <button className="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all border border-white/10 flex justify-between items-center px-4 group">
                    <span>Export Segment List (CSV)</span>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                 </button>
                 <button className="w-full mt-3 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all border border-white/10 flex justify-between items-center px-4 group">
                    <span>Export Full Report (PDF)</span>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
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
      <div className="glass-card p-8 h-full relative cursor-pointer group flex flex-col" onClick={() => setIsExpanded(true)}>
        <div className="absolute inset-0 bg-blue-500/[0.04] opacity-0 group-hover:opacity-100 transition duration-500 rounded-xl pointer-events-none" />
        
        <div className="flex items-start justify-between mb-8 border-b border-white/10 pb-4 relative z-10">
          <div>
             <h2 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
               Segment Risk Heatmap
             </h2>
             <p className="text-sm text-slate-400 mt-1">Churn vulnerability mapped by Region × Plan</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:text-white group-hover:bg-blue-600 transition-all border border-white/10 shadow-sm relative z-10 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.6)] group-hover:scale-110">
             <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </div>
        </div>
        
        <div className="flex-1 w-full h-full flex items-center justify-center relative z-10 pointer-events-none -ml-4">
           {chartData.length > 0 ? <SegmentHeatmapChart data={chartData} /> : <div className="text-slate-500 text-sm ml-4">No segment data available to map.</div>}
        </div>
      </div>
    </>
  )
}
