import { Trophy } from 'lucide-react'
import { ModelOut } from '../../types/api'

export function ModelComparisonTable({ models }: { models: ModelOut[] }) {
  if (!models.length) return null

  return (
    <div className="bg-[#0F1629] border border-[#1E2A45] rounded-xl overflow-hidden shadow-lg h-full flex flex-col">
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-[#141E35] text-slate-400 text-xs tracking-wider uppercase border-b border-[#1E2A45]">
              <th className="px-6 py-5 font-semibold">Model Architecture</th>
              <th className="px-6 py-5 font-semibold">Test AUC</th>
              <th className="px-6 py-5 font-semibold">Val AUC</th>
              <th className="px-6 py-5 font-semibold">F1 Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E2A45]">
            {models.map((model, i) => {
              const isWinner = i === 0;
              return (
                <tr key={model.model_name} className={`text-slate-300 text-sm hover:bg-[#1E2A45]/50 transition ${isWinner ? 'bg-blue-900/10' : ''}`}>
                  <td className="px-6 py-5 font-medium flex items-center gap-3">
                    {isWinner ? <Trophy className="w-5 h-5 text-blue-400 shrink-0" /> : <div className="w-5 shrink-0" />}
                    <span className={isWinner ? 'text-white font-bold' : ''}>{model.model_name}</span>
                  </td>
                  <td className={`px-6 py-5 font-mono ${isWinner ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                    {model.test_auc?.toFixed(3) || '-'}
                  </td>
                  <td className="px-6 py-5 font-mono text-slate-400">{model.val_auc?.toFixed(3) || '-'}</td>
                  <td className="px-6 py-5 font-mono text-blue-400/80">{model.test_f1?.toFixed(3) || '-'}</td>
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
