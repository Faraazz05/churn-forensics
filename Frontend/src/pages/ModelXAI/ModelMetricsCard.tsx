import { CheckCircle } from 'lucide-react'
import { ModelOut } from '../../types/api'

export function ModelMetricsCard({ bestModel }: { bestModel?: ModelOut }) {
  if (!bestModel) return null
  
  return (
    <div className="bg-gradient-to-br from-[#141E35] to-[#0A0D1A] border-2 border-blue-500/50 rounded-xl p-8 shadow-xl relative overflow-hidden h-full flex flex-col justify-center">
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="flex items-center gap-2 mb-6 text-blue-400">
        <CheckCircle className="w-5 h-5" />
        <span className="font-semibold tracking-wide uppercase text-xs">Winning Model</span>
      </div>
      
      <h3 className="text-2xl font-bold text-white mb-8 border-b border-[#1E2A45] pb-6">{bestModel.model_name}</h3>
      
      <div className="space-y-5">
        <div className="flex justify-between items-center">
          <span className="text-slate-400 font-medium tracking-wide">Test AUC</span>
          <span className="font-mono text-2xl font-bold text-emerald-400 bg-emerald-900/20 px-3 py-1 rounded">{bestModel.test_auc?.toFixed(3) || 'N/A'}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400 font-medium tracking-wide">Test F1-Score</span>
          <span className="font-mono text-xl text-blue-300">{bestModel.test_f1?.toFixed(3) || 'N/A'}</span>
        </div>
        <div className="flex justify-between items-center pt-5 border-t border-[#1E2A45] mt-2">
          <span className="text-slate-500 font-medium tracking-wide">Val AUC</span>
          <span className="font-mono text-lg text-slate-400">{bestModel.val_auc?.toFixed(3) || 'N/A'}</span>
        </div>
      </div>
    </div>
  )
}
