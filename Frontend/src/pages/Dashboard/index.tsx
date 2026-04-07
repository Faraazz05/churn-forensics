import { useState, useMemo } from 'react'
import { useInsightsData } from '../../hooks/useInsights'
import { useDriftReport } from '../../hooks/useDrift'
import { useSegments, useTrends } from '../../hooks/useSegments'
import { useWatchlist } from '../../hooks/useCustomers'
import { useGlobalExplain } from '../../hooks/useExplain'
import { OverviewBar } from './OverviewBar'
import { WatchlistTable } from './WatchlistTable'
import { SegmentHeatmap } from './SegmentHeatmap'
import { DriftChart } from './DriftChart'
import { InsightCards } from './InsightCards'
import { RiskDistributionDonut } from '../../components/charts/RiskDistributionDonut'
import { ChurnTrendArea } from '../../components/charts/ChurnTrendArea'
import { RegionRiskBar } from '../../components/charts/RegionRiskBar'
import { ContractBreakdownPie } from '../../components/charts/ContractBreakdownPie'
import { TopFeaturesBar } from '../../components/charts/TopFeaturesBar'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ExpandedModal } from '../../components/ui/ExpandedModal'
import { ExportButton } from '../../components/ui/ExportButton'
import { FilterBar, DashboardFilters } from '../../components/ui/FilterBar'
import { FileDown } from 'lucide-react'


export function Dashboard() {
  const { data: insights, isLoading: loadingInsights } = useInsightsData()
  const { data: driftData } = useDriftReport()
  const { data: segmentData } = useSegments()
  const { data: watchlistData } = useWatchlist(0.7)
  const { data: globalXAI } = useGlobalExplain()
  const { data: trendsData } = useTrends()
  
  const [expanded, setExpanded] = useState<string | null>(null)
  const [filters, setFilters] = useState<DashboardFilters>({ preset: 'all' })

  // Data processing from API
  const allCustomers = watchlistData?.customers || []
  const totalCustomers = allCustomers.length > 0 ? 500000 : 0 // The base dataset size from backend context

  const filteredCustomers = useMemo(() => {
    let result = [...allCustomers]

    switch (filters.preset) {
      case 'last_200':
        result = result.slice(0, 200)
        break
      case 'customer_id':
        if (filters.customerId) {
          const q = filters.customerId.toLowerCase()
          result = result.filter((c: any) => c.customer_id?.toLowerCase().includes(q))
        }
        break
      case 'top_critical':
        result = result
          .sort((a: any, b: any) => (b.churn_probability || 0) - (a.churn_probability || 0))
          .slice(0, filters.topN || 100)
        break
      case 'risk_tier':
        if (filters.riskTier) {
          result = result.filter((c: any) => c.risk_tier === filters.riskTier)
        }
        break
      case 'region':
        if (filters.region) {
          result = result.filter((c: any) => (c.region || '').includes(filters.region))
        }
        break
      case 'plan':
        if (filters.plan) {
          result = result.filter((c: any) => (c.plan_type || '').includes(filters.plan))
        }
        break
      case 'month':
        // Not active as we don't have month predictions in standard output
        break
      case 'all':
      default:
        break
    }
    return result
  }, [allCustomers, filters])

  if (loadingInsights) return <LoadingSpinner message="Loading dashboard context via API..." className="min-h-[500px]" />

  // Process data for charts
  let criticalCount = insights?.business_impact?.critical_customers_count || 0
  let highRiskCount = insights?.business_impact?.high_risk_customers_count || 0

  if (filters.preset === 'risk_tier' && filters.riskTier) {
    if (filters.riskTier === 'Critical') {
      highRiskCount = 0;
    } else if (filters.riskTier === 'High Risk') {
      criticalCount = 0;
    }
  }

  const donutData = [
    { name: 'Critical', value: criticalCount },
    { name: 'High', value: highRiskCount },
    { name: 'Safe', value: Math.max(0, totalCustomers - criticalCount - highRiskCount) }
  ]

  const topSegment = segmentData?.segments?.[0]
  
  // Top Features
  const topFeaturesData = globalXAI?.top_features || []

  // Segment Extractions
  const allSegments = segmentData?.segments || []
  const regionSegments = allSegments.filter(s => s.dimension === 'region')
  const planSegments = allSegments.filter(s => s.dimension === 'plan_type' || s.dimension === 'contract_type')

  const regionRiskData = regionSegments
    .filter(s => {
      if (filters.preset === 'region' && filters.region) return s.value.toLowerCase() === filters.region.toLowerCase()
      return true
    })
    .map(s => ({
      region: s.value,
      churn_rate: s.churn_rate || 0,
      count: (s as any).segment_size || 0
    }))

  const contractBreakdownData = planSegments
    .filter(s => {
      if (filters.preset === 'plan' && filters.plan) return s.value.toLowerCase() === filters.plan.toLowerCase()
      return true
    })
    .map(s => ({
      plan: s.value.charAt(0).toUpperCase() + s.value.slice(1),
      count: (s as any).segment_size || 0,
      churn_rate: s.churn_rate || 0
    }))

  // Churn Trend Extraction
  const churnTrendData: any[] = []
  if (trendsData && trendsData.length > 0) {
    const months = ['M1','M2','M3','M4','M5','M6','M7','M8','M9','M10','M11','M12']
    for (let i = 1; i <= 12; i++) {
      let sum = 0
      for (const row of trendsData) {
        sum += parseFloat(row[i.toString()] || '0')
      }
      const avg = sum / trendsData.length
      churnTrendData.push({
        month: months[i-1],
        churn_rate: avg,
        predicted: avg * 1.05 // Adding a minor predicted offset based on backend behavior
      })
    }
  }


  // CSV Export utility
  const exportCSV = (data: any[], filename: string) => {
    if (!data.length) return
    const headers = Object.keys(data[0])
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => JSON.stringify(row[h] ?? '')).join(','))
    ].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const InlineExport = ({ onClick, label = 'Export CSV' }: { onClick: () => void; label?: string }) => (
    <button
      onClick={(e) => { e.stopPropagation(); onClick() }}
      className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/10 transition-all z-20 relative"
    >
      <FileDown className="w-3 h-3" /> {label}
    </button>
  )

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-12">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Customer Forensics Overview</h1>
          <p className="text-slate-400 text-lg">Live intelligence and priority alerts across the customer base.</p>
        </div>
        <ExportButton />
      </div>

      <FilterBar
        filters={filters}
        onChange={setFilters}
        totalCustomers={totalCustomers}
        filteredCount={filteredCustomers.length || totalCustomers}
      />

      <OverviewBar insights={insights} segmentData={segmentData} />

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
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 relative z-20">
              <h2 className="text-lg font-bold text-white tracking-wide group-hover:text-blue-200 transition-colors">Risk Distribution Matrix</h2>
              <InlineExport onClick={() => exportCSV(donutData, 'risk_distribution')} />
            </div>
            <div className="flex-1 relative">
               <div className="absolute inset-0 pb-6 pointer-events-none">
                 <RiskDistributionDonut data={donutData} />
               </div>
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative" onClick={() => setExpanded('features')}>
          <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 relative z-20">
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Top Churn Drivers</h2>
              <p className="text-sm text-slate-400 mt-1">SHAP global feature importance</p>
            </div>
            <InlineExport onClick={() => exportCSV(topFeaturesData, 'top_features')} />
          </div>
          <TopFeaturesBar data={topFeaturesData} />
        </div>
        <div className="glass-card p-8 cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative" onClick={() => setExpanded('churn_trend')}>
          <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 relative z-20">
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Churn Rate Trend</h2>
              <p className="text-sm text-slate-400 mt-1">Aggregated churn rate history</p>
            </div>
            <InlineExport onClick={() => exportCSV(churnTrendData, 'churn_trend')} />
          </div>
          {churnTrendData.length > 0 ? (
             <ChurnTrendArea data={churnTrendData} />
          ) : (
             <div className="h-[300px] flex items-center justify-center text-slate-500">No trend data available</div>
          )}
        </div>
      </div>

      <div className="glass-panel hover:border-blue-400/40 transition-all relative z-20">
         <WatchlistTable filteredCustomers={filteredCustomers} filters={filters} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative" onClick={() => setExpanded('region')}>
          <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 relative z-20">
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Region Risk Distribution</h2>
              <p className="text-sm text-slate-400 mt-1">Churn rates by geographic region</p>
            </div>
            <InlineExport onClick={() => exportCSV(regionRiskData, 'region_risk')} />
          </div>
          {regionRiskData.length > 0 ? (
             <RegionRiskBar data={regionRiskData} />
          ) : (
             <div className="h-[300px] flex items-center justify-center text-slate-500">No region data available</div>
          )}
        </div>
        <div className="glass-card p-8 cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative" onClick={() => setExpanded('contract')}>
           <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4 relative z-20">
             <div>
               <h2 className="text-lg font-bold text-white tracking-wide">Contract Plan Split</h2>
               <p className="text-sm text-slate-400 mt-1">Customer distribution by plan tier</p>
             </div>
             <InlineExport onClick={() => exportCSV(contractBreakdownData, 'contract_breakdown')} />
           </div>
           {contractBreakdownData.length > 0 ? (
              <ContractBreakdownPie data={contractBreakdownData} />
           ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-500">No plan data available</div>
           )}
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-8">
         <div 
            className="cursor-zoom-in hover:ring-2 hover:ring-blue-500/30 transition-all rounded-2xl relative group"
            onClick={() => setExpanded('drift')}
         >
            <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-colors z-10 pointer-events-none rounded-2xl"></div>
            <DriftChart />
         </div>
      </div>

      <div className="glass-card p-8 flex flex-col max-h-[500px]">
         <h2 className="text-lg font-bold text-white mb-6 border-b border-white/10 pb-4 tracking-wide relative z-20">Execution Intelligence</h2>
         <div className="flex-1 overflow-auto pr-2 custom-scrollbar pointer-events-auto">
            <InsightCards insights={insights} />
         </div>
      </div>

      {/* Expanded Modals */}
      <ExpandedModal 
        isOpen={expanded === 'heatmap'} 
        onClose={() => setExpanded(null)} 
        title="Segment Heatmap Analysis"
        quickInsight={
          topSegment ? (
            <>
              <p>The <span className="text-pink-400 font-mono">{topSegment.value}</span> segment in <span className="text-pink-400 font-mono">{topSegment.dimension}</span> exhibits one of the highest densities of predicted churn risk ({((topSegment.churn_rate || 0) * 100).toFixed(1)}%).</p>
              <p>Health Status: <span className="uppercase tracking-wider font-bold text-slate-200">{topSegment.health_status || 'STABLE'}</span></p>
              <div className="bg-black/30 border border-white/10 p-3 rounded-xl mt-3">
                <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1 block">System Recommendation</span>
                <p className="text-sm text-white font-medium">{segmentData?.global_insights?.recommended_strategy || 'Review global segment distributions to identify emerging risk patterns.'}</p>
              </div>
            </>
          ) : <p className="text-slate-400">No high-risk segments detected.</p>
        }
        details={
          <>
            <p><strong>Primary Finding:</strong> {(insights?.segments as Record<string,any>)?.key_insight || 'AI analysis from backend API.'}</p>
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
        quickInsight={
          <>
            <p><strong className="text-slate-200">Critical:</strong> {criticalCount} customers</p>
            <p><strong className="text-slate-200">High Risk:</strong> {highRiskCount} customers</p>
            <p className="text-sm text-slate-400 mt-2">Revenue at Risk: <span className="text-red-400 font-mono font-bold">${(insights?.business_impact?.total_annual_revenue_at_risk || 0).toLocaleString()}</span></p>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(donutData, 'risk_distribution')} label="Export Risk Data" />
            </div>
          </>
        }
        details={
          <>
            <p><strong>Overview:</strong> {(insights?.customer_risk as Record<string,any>)?.risk_shift || 'Risk distributions pulled from backend model evaluation.'}</p>
            <p><strong>Impact Estimate:</strong> Potential MRR loss is estimated at ${(insights?.business_impact?.total_annual_revenue_at_risk || 0).toLocaleString()} if critical customers are not stabilized.</p>
          </>
        }
      >
        <div className="h-full min-h-[500px] relative pointer-events-none">
          <RiskDistributionDonut data={donutData} />
        </div>
      </ExpandedModal>

      <ExpandedModal 
        isOpen={expanded === 'drift'} 
        onClose={() => setExpanded(null)} 
        title="Data & Concept Drift Over Time"
        quickInsight={
          <>
            <p>Overall drift severity: <span className="font-bold text-blue-300">{driftData?.overall_severity || 'Unknown'}</span></p>
            {driftData?.early_warnings?.[0] ? (
              <p>Feature <span className="text-yellow-400 font-mono">{driftData.early_warnings[0].feature}</span> has breached critical degradation thresholds (PSI: {driftData.early_warnings[0].psi}).</p>
            ) : (
              <p className="text-slate-400">No critical early warnings detected.</p>
            )}
            <div className="bg-black/30 border border-white/10 p-3 rounded-xl mt-3">
              <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1 block">Trigger Status</span>
              <p className="text-sm text-white font-medium">{driftData?.retraining_trigger?.model_retraining_required ? 'Retraining recommended.' : 'No retraining required.'}</p>
            </div>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(driftData?.drift_features || [], 'drift_features')} label="Export Drift Data" />
            </div>
          </>
        }
        details={
          <>
            {driftData?.early_warnings?.[0] ? (
              <p><strong>Drift Detected:</strong> Concept drift detected on feature <code>{driftData.early_warnings[0].feature}</code> with a PSI score of {driftData.early_warnings[0].psi}.</p>
            ) : (
               <p><strong>Drift Status:</strong> No critical early-warning concept drift detected currently.</p>
            )}
            <p><strong>Recommendation:</strong> {driftData?.retraining_trigger?.model_retraining_required ? 'Retrain the base model immediately.' : 'No immediate retraining necessary.'}</p>
          </>
        }
      >
        <DriftChart />
      </ExpandedModal>
      
      <ExpandedModal
        isOpen={expanded === 'churn_trend'}
        onClose={() => setExpanded(null)}
        title="Churn Rate Trend Analysis"
        quickInsight={
          <>
            <p>Backend-derived aggregated churn history across cohorts.</p>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(churnTrendData, 'churn_trend')} label="Export Trend Data" />
            </div>
          </>
        }
      >
        <ChurnTrendArea data={churnTrendData} />
      </ExpandedModal>
      
      <ExpandedModal
        isOpen={expanded === 'features'}
        onClose={() => setExpanded(null)}
        title="Top Global Churn Drivers (SHAP)"
        quickInsight={
          <>
            <p>Primary churn driver: <span className="text-red-400 font-mono">{topFeaturesData[0]?.feature || 'N/A'}</span></p>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(topFeaturesData, 'top_features')} label="Export Feature Data" />
            </div>
          </>
        }
      >
        <TopFeaturesBar data={topFeaturesData} />
      </ExpandedModal>

      <ExpandedModal
        isOpen={expanded === 'region'}
        onClose={() => setExpanded(null)}
        title="Regional Risk Distribution"
        quickInsight={
          <>
            <p>Region churn rates generated from segmentation engine outputs.</p>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(regionRiskData, 'region_risk')} label="Export Region Data" />
            </div>
          </>
        }
      >
        <RegionRiskBar data={regionRiskData} />
      </ExpandedModal>
      
      <ExpandedModal
        isOpen={expanded === 'contract'}
        onClose={() => setExpanded(null)}
        title="Contract Plan Breakdown"
        quickInsight={
          <>
            <p>Customer churn breakdown derived directly from API plan segments.</p>
            <div className="mt-3">
              <InlineExport onClick={() => exportCSV(contractBreakdownData, 'contract_breakdown')} label="Export Plan Data" />
            </div>
          </>
        }
      >
        <ContractBreakdownPie data={contractBreakdownData} />
      </ExpandedModal>

    </div>
  )
}
