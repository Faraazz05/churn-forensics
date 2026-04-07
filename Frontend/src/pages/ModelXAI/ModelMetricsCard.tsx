import { CheckCircle, Info } from 'lucide-react'
import { ModelOut } from '../../types/api'
import { useState } from 'react'

export function ModelMetricsCard({ bestModel }: { bestModel?: ModelOut }) {
  const [showInfo, setShowInfo] = useState(false)

  if (!bestModel) return null

  const valTestGap = bestModel.val_auc && bestModel.test_auc
    ? Math.abs(bestModel.val_auc - bestModel.test_auc)
    : null

  const getGapStatus = () => {
    if (!valTestGap) return null
    if (valTestGap < 0.01) return { text: 'Excellent generalization', color: 'text-green-400' }
    if (valTestGap < 0.03) return { text: 'Good generalization', color: 'text-yellow-400' }
    return { text: 'Possible overfitting', color: 'text-red-400' }
  }

  const gapStatus = getGapStatus()
  
  return (
    <div className="bg-gradient-to-br from-[#141E35] to-[#0A0D1A] border-2 border-blue-500/50 rounded-xl p-8 shadow-xl relative overflow-hidden h-full flex flex-col justify-center">
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="flex items-center gap-2 mb-6 text-blue-400">
        <CheckCircle className="w-5 h-5" />
        <span className="font-semibold tracking-wide uppercase text-xs">Winning Model</span>
      </div>
      
      <h3 className="text-2xl font-bold text-white mb-8 border-b border-[#1E2A45] pb-6">{bestModel.model_name}</h3>
      
      <div className="space-y-5">
        {/* Test Metrics */}
        <div>
          <div className="text-[10px] uppercase tracking-widest text-blue-400/60 font-bold mb-2">Test Set (Holdout)</div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 font-medium tracking-wide">Test AUC</span>
            <span className="font-mono text-2xl font-bold text-emerald-400 bg-emerald-900/20 px-3 py-1 rounded">{bestModel.test_auc?.toFixed(3) || 'N/A'}</span>
          </div>
          <div className="flex justify-between items-center mt-3">
            <span className="text-slate-400 font-medium tracking-wide">Test F1-Score</span>
            <span className="font-mono text-xl text-blue-300">{bestModel.test_f1?.toFixed(3) || 'N/A'}</span>
          </div>
        </div>

        {/* Validation Metrics */}
        <div className="pt-5 border-t border-[#1E2A45]">
          <div className="text-[10px] uppercase tracking-widest text-purple-400/60 font-bold mb-2">Validation (Cross-Val)</div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500 font-medium tracking-wide">Val AUC</span>
            <span className="font-mono text-lg text-slate-400">{bestModel.val_auc?.toFixed(3) || 'N/A'}</span>
          </div>
          {bestModel.val_f1 && (
            <div className="flex justify-between items-center mt-2">
              <span className="text-slate-500 font-medium tracking-wide">Val F1</span>
              <span className="font-mono text-lg text-slate-400">{bestModel.val_f1?.toFixed(3)}</span>
            </div>
          )}
        </div>

        {/* Generalization Status */}
        {gapStatus && (
          <div className="pt-5 border-t border-[#1E2A45]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-semibold ${gapStatus.color}`}>{gapStatus.text}</span>
                <button
                  className="text-slate-500 hover:text-slate-300 transition-colors relative"
                  onMouseEnter={() => setShowInfo(true)}
                  onMouseLeave={() => setShowInfo(false)}
                >
                  <Info className="w-3.5 h-3.5" />
                  {showInfo && (
                    <div className="absolute z-50 left-6 -top-1 bg-[#0A0D1A] border border-[#1E2A45] rounded-lg p-3 text-xs text-slate-300 shadow-xl w-52">
                      <p className="font-semibold text-slate-200 mb-1">Val-Test Gap: {valTestGap?.toFixed(4)}</p>
                      <p className="text-slate-500">A small gap between validation and test AUC indicates the model generalizes well to unseen data.</p>
                    </div>
                  )}
                </button>
              </div>
              <span className="text-xs text-slate-600 font-mono">Δ {valTestGap?.toFixed(4)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
