import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useModels } from '../../hooks/useModels'
import { useGlobalExplain } from '../../hooks/useExplain'
import { ModelMetricsCard } from './ModelMetricsCard'
import { ModelComparisonTable } from './ModelComparisonTable'
import { XAIMethodsPanel } from './XAIMethodsPanel'
import { XAIConfidenceBar } from './XAIConfidenceBar'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'

export function ModelXAI() {
  const navigate = useNavigate()
  const { data: modelsData, isLoading: modelsLoading } = useModels()
  const { data: xaiData, isLoading: xaiLoading } = useGlobalExplain()

  if (modelsLoading || xaiLoading) return <LoadingSpinner message="Loading model context..." />

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="mb-10">
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-3 drop-shadow-sm">Model Configuration & Explainable AI (XAI)</h1>
        <p className="text-slate-300 text-lg">Validate the selected machine learning model and review the Explainable AI (XAI) configuration, identifying primary and secondary interpretability methods.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="glass-active p-6 text-center relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500/0 via-blue-400 to-blue-500/0"></div>
          <div className="text-3xl font-bold font-mono text-white mb-1 drop-shadow-[0_0_10px_rgba(59,130,246,0.8)]">XGBoost_v2</div>
          <div className="text-blue-400 font-medium">Primary Selected Model</div>
        </div>
        <div className="glass-card p-6 text-center border-emerald-500/50 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.3)] relative overflow-hidden ring-1 ring-emerald-500/50">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500/0 via-emerald-400 to-emerald-500/0"></div>
          <div className="text-3xl font-bold font-mono text-emerald-400 mb-1 pt-2 drop-shadow-[0_0_10px_rgba(16,185,129,0.8)]">SHAP</div>
          <div className="text-slate-300 font-medium tracking-wide">Primary XAI Method</div>
        </div>
        <div className="glass-card p-6 text-center relative overflow-hidden">
          <div className="text-3xl font-bold font-mono text-slate-300 mb-1 pt-2">LIME & Anchor</div>
          <div className="text-slate-400 font-medium tracking-wide">Secondary XAI Methods</div>
        </div>
      </div>

      <div className="mb-16">
        <h2 className="text-2xl font-bold text-slate-100 mb-6 border-b border-[#1E2A45] pb-4">AutoML Selection</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <ModelMetricsCard bestModel={modelsData?.best_model || {
                model_name: 'XGBoost_v2', test_auc: 0.941, test_f1: 0.88, val_auc: 0.945, is_active: true
            }} />
          </div>
          <div className="lg:col-span-2">
            <ModelComparisonTable models={modelsData?.all_models || [
                { model_name: 'XGBoost_v2', test_auc: 0.941, val_auc: 0.945, test_f1: 0.88, is_active: true },
                { model_name: 'RandomForest', test_auc: 0.890, val_auc: 0.895, test_f1: 0.84, is_active: false },
                { model_name: 'Logistic_Regression', test_auc: 0.830, val_auc: 0.835, test_f1: 0.76, is_active: false },
            ]} />
          </div>
        </div>
      </div>

      <div className="mb-16">
        <h2 className="text-2xl font-bold text-slate-100 mb-6 border-b border-white/10 pb-4">XAI Consensus Configuration</h2>
        <XAIMethodsPanel />
        <div className="mt-8">
           <XAIConfidenceBar data={xaiData} />
        </div>
      </div>
    </div>
  )
}
