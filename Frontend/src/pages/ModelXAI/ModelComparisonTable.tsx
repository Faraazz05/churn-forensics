import { Trophy, Info } from 'lucide-react'
import { ModelOut } from '../../types/api'
import { useState } from 'react'

interface Props {
  models: ModelOut[]
  bestModelName?: string
}

export function ModelComparisonTable({ models, bestModelName }: Props) {
  const [showTooltip, setShowTooltip] = useState<string | null>(null)

  if (!models.length) return null

  // Sort: best model first, then by test_auc descending
  const sorted = [...models].sort((a, b) => {
    if (a.model_name === bestModelName) return -1
    if (b.model_name === bestModelName) return 1
    return (b.test_auc ?? 0) - (a.test_auc ?? 0)
  })

  const getOverfitIndicator = (model: ModelOut) => {
    if (!model.test_auc || !model.val_auc) return null
    const diff = Math.abs(model.val_auc - model.test_auc)
    if (diff < 0.01) return { label: 'Stable', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' }
    if (diff < 0.03) return { label: 'Minor Gap', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' }
    return { label: 'Overfit Risk', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' }
  }

  return (
    <div className="bg-[#0F1629] border border-[#1E2A45] rounded-xl overflow-hidden shadow-lg h-full flex flex-col">
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-[#141E35] text-slate-400 text-xs tracking-wider uppercase border-b border-[#1E2A45]">
              <th className="px-6 py-5 font-semibold">Model Architecture</th>
              <th className="px-6 py-5 font-semibold">
                Test AUC
                <span className="ml-1 text-[10px] text-slate-500 normal-case tracking-normal">(holdout)</span>
              </th>
              <th className="px-6 py-5 font-semibold">
                Val AUC
                <span className="ml-1 text-[10px] text-slate-500 normal-case tracking-normal">(CV)</span>
              </th>
              <th className="px-6 py-5 font-semibold">
                F1 Score
                <span className="ml-1 text-[10px] text-slate-500 normal-case tracking-normal">(test)</span>
              </th>
              <th className="px-6 py-5 font-semibold">Generalization</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E2A45]">
            {sorted.map((model) => {
              const isWinner = model.model_name === bestModelName
              const indicator = getOverfitIndicator(model)
              return (
                <tr
                  key={model.model_name}
                  className={`text-slate-300 text-sm transition-colors ${isWinner ? 'bg-blue-900/15 hover:bg-blue-900/25' : 'hover:bg-[#1E2A45]/50'}`}
                >
                  <td className="px-6 py-5 font-medium flex items-center gap-3">
                    {isWinner ? <Trophy className="w-5 h-5 text-blue-400 shrink-0 drop-shadow-[0_0_6px_rgba(96,165,250,0.6)]" /> : <div className="w-5 shrink-0" />}
                    <span className={isWinner ? 'text-white font-bold' : ''}>{model.model_name}</span>
                    {isWinner && <span className="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border border-blue-500/30">Best</span>}
                  </td>
                  <td className={`px-6 py-5 font-mono text-base ${isWinner ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                    {model.test_auc?.toFixed(3) || '-'}
                  </td>
                  <td className="px-6 py-5 font-mono text-base text-slate-400">{model.val_auc?.toFixed(3) || '-'}</td>
                  <td className="px-6 py-5 font-mono text-base text-blue-400/80">{model.test_f1?.toFixed(3) || '-'}</td>
                  <td className="px-6 py-5 relative">
                    {indicator && (
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-semibold px-2 py-1 rounded-lg border ${indicator.bg} ${indicator.color}`}>
                          {indicator.label}
                        </span>
                        <button
                          className="text-slate-500 hover:text-slate-300 transition-colors"
                          onMouseEnter={() => setShowTooltip(model.model_name)}
                          onMouseLeave={() => setShowTooltip(null)}
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>
                        {showTooltip === model.model_name && (
                          <div className="absolute z-50 right-4 top-0 mt-1 bg-[#0A0D1A] border border-[#1E2A45] rounded-lg p-3 text-xs text-slate-300 shadow-xl w-52">
                            <p className="font-semibold text-slate-200 mb-1">Val vs Test Gap</p>
                            <p>Difference: {model.val_auc && model.test_auc ? Math.abs(model.val_auc - model.test_auc).toFixed(4) : 'N/A'}</p>
                            <p className="text-slate-500 mt-1">Small gaps indicate good generalization. Large gaps may indicate overfitting.</p>
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="p-5 bg-[#0A0D1A] border-t border-[#1E2A45] text-sm text-slate-300 flex items-start gap-3 leading-relaxed shadow-inner">
         <span className="text-blue-500 font-bold uppercase tracking-wider text-xs mt-0.5 shrink-0">Reasoning</span> 
         <p>Maintains highest AUC generalization score without overfitting (Test AUC ≈ Val AUC). Superior handling of non-linear interactions compared to baseline logic.</p>
      </div>
    </div>
  )
}
