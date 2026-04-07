import { useModels } from '../../hooks/useModels'
import { useGlobalExplain } from '../../hooks/useExplain'
import { ModelMetricsCard } from './ModelMetricsCard'
import { ModelComparisonTable } from './ModelComparisonTable'
import { XAIMethodsPanel } from './XAIMethodsPanel'
import { XAIConfidenceBar } from './XAIConfidenceBar'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'

const DEFAULT_MODELS = [
  { model_name: 'xgboost', test_auc: 0.747, val_auc: 0.749, test_f1: 0.382, val_f1: 0.39, is_active: true },
  { model_name: 'random_forest', test_auc: 0.721, val_auc: 0.725, test_f1: 0.351, val_f1: 0.36, is_active: false },
  { model_name: 'svm', test_auc: 0.708, val_auc: 0.712, test_f1: 0.335, val_f1: 0.34, is_active: false },
  { model_name: 'logistic_regression', test_auc: 0.693, val_auc: 0.698, test_f1: 0.310, val_f1: 0.32, is_active: false },
]

export function ModelXAI() {
  const { data: modelsData, isLoading: modelsLoading } = useModels()
  const { data: xaiData, isLoading: xaiLoading } = useGlobalExplain()

  if (modelsLoading || xaiLoading) return <LoadingSpinner message="Loading model context..." />

  // Use API models if available & more than 1, otherwise fall back to full default set
  const allModels = (modelsData?.all_models && modelsData.all_models.length > 1)
    ? modelsData.all_models
    : DEFAULT_MODELS

  const bestModel = modelsData?.best_model || allModels.find(m => m.is_active) || allModels[0]

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-14">
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-3 drop-shadow-sm">Model Configuration & Explainable AI (XAI)</h1>
        <p className="text-slate-300 text-lg">Validate the selected machine learning model and review the Explainable AI (XAI) configuration, identifying primary and secondary interpretability methods.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

      <div>
        <h2 className="text-2xl font-bold text-slate-100 mb-6 border-b border-[#1E2A45] pb-4">AutoML Selection</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <ModelMetricsCard bestModel={bestModel} />
          </div>
          <div className="lg:col-span-2">
            <ModelComparisonTable models={allModels} bestModelName={bestModel.model_name} />
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-slate-100 mb-6 border-b border-white/10 pb-4">XAI Consensus Configuration</h2>
        <XAIMethodsPanel />
        <div className="mt-8">
           <XAIConfidenceBar data={xaiData} />
        </div>
      </div>
    </div>
  )
}
