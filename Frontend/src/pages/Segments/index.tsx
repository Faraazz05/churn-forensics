import { useSegments } from '../../hooks/useSegments'
import { SegmentHeatmapChart } from '../../components/charts/SegmentHeatmapChart'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { RevenueBanner } from './RevenueBanner'
import { SegmentCard } from './SegmentCard'

export function SegmentsPage() {
  const { data, isLoading } = useSegments()
  
  if (isLoading) return <LoadingSpinner className="min-h-[400px]" />
  
  const mockData = [{ x: 'Enterprise', y: 'NA', value: 0.12 }, { x: 'Starter', y: 'NA', value: 0.65 }]
  const chartData = data?.segments?.map(s => ({ x: s.dimension, y: s.value, value: s.churn_rate ?? 0 })) || mockData;

  const degradingSegments = data?.global_insights?.top_degrading_segments || data?.segments?.filter(s => s.health_status === 'degrading') || [];
  const topSegments = (data?.segments || []).slice(0, 4);

  return (
    <div className="max-w-7xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Segment Intelligence</h1>
        <p className="text-slate-400 text-lg">Analyze churn risk across customer dimensions</p>
      </div>
      
      <div className="mb-8">
        <RevenueBanner 
          revenueAtRisk={data?.global_insights?.total_revenue_at_risk} 
          nDegrading={data?.global_insights?.n_degrading} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-2 bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl min-h-[500px] flex flex-col">
            <h2 className="text-xl font-bold text-white mb-6 border-b border-[#1E2A45] pb-4">Cohort Risk Grid</h2>
            <div className="flex-1">
              <SegmentHeatmapChart data={chartData} />
            </div>
         </div>
         
         <div className="lg:col-span-1 space-y-6 flex flex-col h-full">
            <div className="flex items-center justify-between border-b border-[#1E2A45] pb-4">
               <h2 className="text-xl font-bold text-white">Top Segments</h2>
               <span className="text-xs font-bold text-slate-400 bg-[#1E2A45] px-2 py-1 rounded">
                 {data?.n_segments || topSegments.length} Total
               </span>
            </div>
            
            <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1 max-h-[500px]">
               {topSegments.map((seg, i) => (
                 <SegmentCard key={i} segment={seg} />
               ))}
               {topSegments.length === 0 && (
                 <div className="p-8 text-center border border-dashed border-[#1E2A45] rounded-xl text-slate-500">
                    No active segments detected.
                 </div>
               )}
            </div>
         </div>
      </div>
    </div>
  )
}
