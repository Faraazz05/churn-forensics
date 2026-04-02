import { useDriftReport } from '../../hooks/useDrift'
import { PSIBarChart } from '../../components/charts/PSIBarChart'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { RetrainingBanner } from './RetrainingBanner'
import { EarlyWarningList } from './EarlyWarningList'

export function DriftAnalysis() {
  const { data, isLoading } = useDriftReport()
  
  if (isLoading) return <LoadingSpinner className="min-h-[400px]" />
  
  const chartData = data?.drift_features
    ? data.drift_features.slice(0, 10).map(f => ({
        feature: f.feature,
        psi: f.psi ?? 0,
        severity: f.drift_severity || (f.psi && f.psi > 0.2 ? 'Critical' : f.psi && f.psi > 0.1 ? 'Warning' : 'Safe')
      }))
    : []

  return (
    <div className="max-w-7xl mx-auto py-8">
      <div className="mb-8">
         <h1 className="text-3xl font-bold text-white mb-2">Concept & Data Drift</h1>
         <p className="text-slate-400 text-lg">Monitor model health and distribution shifts over time</p>
      </div>

      <RetrainingBanner trigger={data?.retraining_trigger || { model_retraining_required: true, reason: 'Multiple high severity drift indicators detected' }} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <div className="lg:col-span-2 flex flex-col gap-8">
            <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl flex-1">
               <h2 className="text-xl font-bold text-white mb-6 border-b border-[#1E2A45] pb-4">Feature PSI Distribution</h2>
               <div className="h-[300px]">
                  {chartData.length > 0 ? (
                    <PSIBarChart data={chartData} />
                  ) : (
                    <div className="h-full flex items-center justify-center text-slate-500 text-sm">No feature drift data available.</div>
                  )}
               </div>
            </div>
         </div>
         
         <div className="lg:col-span-1 min-h-[500px]">
            <EarlyWarningList predrifts={data?.early_warnings} />
         </div>
      </div>
    </div>
  )
}
