import { useDriftReport } from '../../hooks/useDrift'
import { DriftTrendLine } from '../../components/charts/DriftTrendLine'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { RetrainingBanner } from './RetrainingBanner'
import { EarlyWarningList } from './EarlyWarningList'

export function DriftAnalysis() {
  const { data, isLoading } = useDriftReport()
  
  if (isLoading) return <LoadingSpinner className="min-h-[400px]" />
  
  const mockTrend = [
    { month: 'Jan', value: 0.02 }, { month: 'Feb', value: 0.05 }, { month: 'Mar', value: 0.12 }, { month: 'Apr', value: 0.24 }
  ]

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
               <h2 className="text-xl font-bold text-white mb-6 border-b border-[#1E2A45] pb-4">Global Drift Trend (PSI)</h2>
               <div className="h-[300px]">
                  <DriftTrendLine data={mockTrend} />
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
