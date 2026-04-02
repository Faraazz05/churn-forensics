import { ChurnProbabilityGauge } from '../../components/charts/ChurnProbabilityGauge'
import { RiskBadge } from '../../components/ui/RiskBadge'
import { PredictionOut } from '../../types/api'

export function PredictionCard({ prediction }: { prediction?: PredictionOut | null }) {
  return (
    <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl flex flex-col min-h-[300px] relative overflow-hidden transition-all hover:border-[#1E2A45]/80 hover:shadow-2xl">
      <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-white tracking-wide">Churn Risk</h2>
        {prediction?.risk_tier && <RiskBadge tier={prediction.risk_tier} />}
      </div>
      <div className="flex-1 flex items-center justify-center py-4">
        <ChurnProbabilityGauge probability={prediction?.churn_probability ?? 0.65} />
      </div>
      {prediction?.model_name && (
        <div className="mt-4 pt-4 border-t border-[#1E2A45]/50 flex justify-between items-center text-xs">
          <span className="text-slate-500">Model used</span>
          <span className="text-blue-400/80 font-mono px-2 py-1 bg-blue-500/10 rounded">{prediction.model_name}</span>
        </div>
      )}
    </div>
  )
}
