import { useState } from 'react'
import { InsightResponse } from '../../types/api'
import { FileText, ArrowRight, LightbulbIcon, X, Sparkles, AlertTriangle } from 'lucide-react'

export function InsightCards({ insights }: { insights?: InsightResponse }) {
  const [selectedInsight, setSelectedInsight] = useState<{title: string, content: string, type: 'brief' | 'rec' | null} | null>(null)

  const executiveText = insights?.executive_summary || 'Overall risk has increased slightly over the past 30 days. Action is required on the top 2 degrading segments associated with enterprise tiers in NA. Model confidence remains stable at 94%.'
  
  const recommendations = insights?.recommendations?.length ? insights.recommendations.map(rec => ({
    action: rec.source === 'rl' ? 'System Action' : 'Review',
    description: rec.description,
    expected_impact: Math.max(0.02, 0.15 - (rec.rank * 0.02))
  })) : [
    { action: 'Review', description: 'Reach out to top 15 Enterprise accounts in Warning state', expected_impact: 0.1 },
    { action: 'Update', description: 'Retrain model on recent API usage features', expected_impact: 0.05 },
    { action: 'Alert', description: 'Investigate anomaly in EMEA region signups', expected_impact: 0.02 },
  ]

  const modal = selectedInsight ? (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-black/60 backdrop-blur-md">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] flex flex-col p-8 md:p-12 rounded-3xl relative shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/20 transition-all animate-in fade-in zoom-in-95 duration-300">
         <button onClick={(e) => { e.stopPropagation(); setSelectedInsight(null) }} className="absolute z-10 top-6 right-6 p-2.5 bg-white/5 hover:bg-white/10 rounded-full text-white transition-all border border-white/10">
           <X className="w-5 h-5" />
         </button>
         
         <div className="flex items-center gap-4 mb-8 pb-8 border-b border-white/10">
           <div className={`p-4 rounded-2xl ${selectedInsight.type === 'brief' ? 'bg-blue-500/20 text-blue-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
              {selectedInsight.type === 'brief' ? <FileText className="w-8 h-8" /> : <LightbulbIcon className="w-8 h-8" />}
           </div>
           <div>
             <h2 className="text-3xl font-bold text-white mb-2">{selectedInsight.title}</h2>
             <p className="text-slate-400 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" /> AI-Generated Intelligence Report
             </p>
           </div>
         </div>
         
         <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar">
           <div className="glass-card p-8 rounded-2xl relative overflow-hidden backdrop-blur-xl bg-gradient-to-br from-white/5 to-transparent">
             <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
             <div className="prose prose-invert prose-blue max-w-none text-lg text-slate-300 leading-relaxed font-light">
                <p>
                  {selectedInsight.content}
                </p>
                {selectedInsight.type === 'rec' && (
                  <div className="mt-8 p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-xl relative overflow-hidden">
                     <AlertTriangle className="w-16 h-16 text-emerald-500/10 absolute -right-2 -bottom-2" />
                     <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">Actionable Impact</h4>
                     <p className="text-emerald-300/80 text-sm">Execution of this recommendation correlates with improved retention probabilities based on historical twin cohorts.</p>
                     <button className="mt-6 px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-white font-bold rounded-lg transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                        Add to Action Plan
                     </button>
                  </div>
                )}
             </div>
           </div>
         </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      {modal}
      <div className="space-y-6">
        <div 
           className="glass-active p-6 cursor-pointer hover:ring-2 hover:ring-blue-400/50 transition-all duration-300 group"
           onClick={() => setSelectedInsight({ title: 'Executive Brief', content: executiveText, type: 'brief' })}
        >
          <div className="flex items-start gap-5">
            <div className="p-3 bg-blue-500/20 rounded-xl shrink-0 border border-blue-400/30">
               <FileText className="w-6 h-6 text-blue-300" />
            </div>
            <div className="flex-1 mt-1">
               <h3 className="font-semibold text-white mb-2 flex items-center justify-between tracking-wide">
                  Executive Brief <ArrowRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-all translate-x-0 group-hover:translate-x-1 text-blue-400" />
               </h3>
               <p className="text-sm text-slate-300 leading-relaxed max-w-lg">
                 {executiveText}
               </p>
            </div>
          </div>
        </div>
        
        <div className="px-2 pt-2">
           <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <LightbulbIcon className="w-4 h-4 text-emerald-400" /> Priority Recommendations
           </h4>
           <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec, i) => (
                <div 
                  key={i} 
                  className="glass-panel p-4 cursor-pointer hover:bg-emerald-500/10 hover:border-emerald-500/40 hover:shadow-[0_0_20px_rgba(16,185,129,0.2)] transition-all flex items-center justify-between"
                  onClick={() => setSelectedInsight({ title: `Recommendation: ${rec.action}`, content: rec.description, type: 'rec' })}
                >
                   <div className="flex gap-4 items-center flex-1">
                      <span className="w-8 h-8 rounded-xl bg-black/30 border border-white/10 text-emerald-400 text-sm font-bold flex items-center justify-center shrink-0 shadow-inner">{i+1}</span>
                      <span className="text-sm text-slate-200 line-clamp-2 leading-relaxed">{rec.description}</span>
                   </div>
                   <div className="ml-4 shrink-0 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-xl shadow-inner relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/0 via-emerald-400/10 to-emerald-400/0"></div>
                      <span className="relative z-10">+{(rec.expected_impact * 100).toFixed(0)}% ROI</span>
                   </div>
                </div>
              ))}
           </div>
        </div>
      </div>
    </>
  )
}
