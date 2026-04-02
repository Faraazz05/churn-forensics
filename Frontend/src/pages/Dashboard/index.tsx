import { useState } from 'react'
import { useInsightsData } from '../../hooks/useInsights'
import { useDriftReport } from '../../hooks/useDrift'
import { OverviewBar } from './OverviewBar'
import { WatchlistTable } from './WatchlistTable'
import { SegmentHeatmap } from './SegmentHeatmap'
import { DriftChart } from './DriftChart'
import { InsightCards } from './InsightCards'
import { RiskDistributionDonut } from '../../components/charts/RiskDistributionDonut'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ExpandedModal } from '../../components/ui/ExpandedModal'

export function Dashboard() {
  const { data: insights, isLoading } = useInsightsData()
  const [expanded, setExpanded] = useState<string | null>(null)
  if (isLoading) return <LoadingSpinner message="Loading dashboard context..." className="min-h-[500px]" />

  const { data: driftData } = useDriftReport()

  const donutData = [
    { name: 'Critical', value: insights?.business_impact?.critical_customers_count ?? 0 },
    { name: 'High', value: insights?.business_impact?.high_risk_customers_count ?? 0 },
    { name: 'Medium', value: insights?.business_impact ? Object.keys(insights.customer_risk as Record<string,any>).length * 4 : 0 },
    { name: 'Safe', value: insights?.business_impact ? Object.keys(insights.customer_risk as Record<string,any>).length * 10 : 0 }
  ]

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Customer Forensics Overview</h1>
        <p className="text-slate-400 text-lg">Live intelligence and priority alerts across the customer base.</p>
      </div>

      <OverviewBar insights={insights} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
         <div 
            className="lg:col-span-3 h-full cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative group"
            onClick={() => setExpanded('heatmap')}
         >
            <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-colors z-10 pointer-events-none rounded-2xl"></div>
            <SegmentHeatmap />
         </div>
         <div 
            className="lg:col-span-2 glass-card p-8 flex flex-col min-h-[400px] cursor-zoom-in hover:border-blue-400/40 transition-all relative group"
            onClick={() => setExpanded('donut')}
         >
            <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-colors z-10 pointer-events-none rounded-2xl"></div>
            <h2 className="text-lg font-bold text-white mb-6 border-b border-white/10 pb-4 tracking-wide group-hover:text-blue-200 transition-colors">Risk Distribution Matrix</h2>
            <div className="flex-1 relative">
               <div className="absolute inset-0 pb-6 pointer-events-none">
                 <RiskDistributionDonut data={donutData} />
               </div>
            </div>
         </div>
      </div>

      <div className="glass-panel hover:border-blue-400/40 transition-all">
         <WatchlistTable />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
         <div 
            className="cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative group"
            onClick={() => setExpanded('drift')}
         >
            <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-colors z-10 pointer-events-none rounded-2xl"></div>
            <DriftChart />
         </div>
         <div className="glass-card p-8 flex flex-col max-h-[500px]">
            <h2 className="text-lg font-bold text-white mb-6 border-b border-white/10 pb-4 tracking-wide">Execution Intelligence</h2>
            <div className="flex-1 overflow-auto pr-2 custom-scrollbar pointer-events-auto">
               <InsightCards insights={insights} />
            </div>
         </div>
      </div>

      {/* Expanded Modals */}
      <ExpandedModal 
        isOpen={expanded === 'heatmap'} 
        onClose={() => setExpanded(null)} 
        title="Segment Heatmap Analysis"
        details={
          <>
            <p><strong>Primary Finding:</strong> {(insights?.segments as Record<string,any>)?.key_insight || 'AI analysis pending.'}</p>
            <p><strong>Executive Summary:</strong> {insights?.executive_summary}</p>
            {insights?.recommendations?.[0] && (
               <p><strong>Actionable Advice:</strong> {insights.recommendations[0].description}</p>
            )}
          </>
        }
      >
        <SegmentHeatmap />
      </ExpandedModal>

      <ExpandedModal 
        isOpen={expanded === 'donut'} 
        onClose={() => setExpanded(null)} 
        title="Risk Distribution Matrix"
        details={
          <>
            <p><strong>Overview:</strong> {(insights?.customer_risk as Record<string,any>)?.risk_shift || 'Risk distributions currently align with historical baselines.'}</p>
            <p><strong>Impact Estimate:</strong> Potential MRR loss is estimated at ${(insights?.business_impact?.total_annual_revenue_at_risk || 0).toLocaleString()} if critical customers are not stabilized.</p>
          </>
        }
      >
        <div className="h-full min-h-[500px] relative">
          <RiskDistributionDonut data={donutData} />
        </div>
      </ExpandedModal>

      <ExpandedModal 
        isOpen={expanded === 'drift'} 
        onClose={() => setExpanded(null)} 
        title="Data & Concept Drift Over Time"
        details={
          <>
            {driftData?.early_warnings?.[0] ? (
              <p><strong>Drift Detected:</strong> Concept drift detected on feature <code>{driftData.early_warnings[0].feature}</code> with a PSI score of {driftData.early_warnings[0].psi}.</p>
            ) : (
               <p><strong>Drift Status:</strong> No critical early-warning concept drift detected currently.</p>
            )}
            <p><strong>Model Status:</strong> {driftData?.overall_severity || 'Unknown'}</p>
            <p><strong>Recommendation:</strong> {driftData?.retraining_trigger?.model_retraining_required ? 'Retrain the base model immediately.' : 'No immediate retraining necessary.'}</p>
          </>
        }
      >
        <DriftChart />
      </ExpandedModal>
    </div>
  )
}
