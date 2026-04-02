import { Database, Activity, BrainCircuit, Trophy, Fingerprint, PieChart, AlertTriangle, Lightbulb, Check, Loader2 } from 'lucide-react'

const ALL_PHASES = [
  { id: 'ingestion', label: 'Data Ingestion', icon: Database, desc: '500,000 rows loaded' },
  { id: 'feature_eng', label: 'Feature Engineering', icon: Activity, desc: '12 analytical features computed' },
  { id: 'model_selection', label: 'AutoML Selection', icon: BrainCircuit, desc: 'Testing XGBoost + Logistic paths' },
  { id: 'best_model', label: 'Model Evaluation', icon: Trophy, desc: 'Winning Model: XGBoost_v2 selected' },
  { id: 'xai', label: 'XAI Generation', icon: Fingerprint, desc: 'Feature attributions computed exactly' },
  { id: 'segments', label: 'Segmentation', icon: PieChart, desc: '14 cohort macro-segments analyzed' },
  { id: 'drift', label: 'Drift Detection', icon: AlertTriangle, desc: '12 features tracked for degradation' },
  { id: 'insights', label: 'Intelligence Layer', icon: Lightbulb, desc: 'Business impact report generated' }
]

export function PipelineStageTracker({ phases, isDone }: { phases: string[], isDone: boolean }) {
  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <h3 className="text-xl font-bold text-blue-400 mb-6 font-mono border-b border-white/10 pb-4">Training & Testing ML Algorithms...</h3>
      <div className="flex-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
        {ALL_PHASES.map((phase, i) => {
          const isCompleted = isDone || phases.includes(phase.id) || phases.length > i;
          const isCurrent = !isCompleted && phases.length === i && !isDone;
          
          return (
            <div key={phase.id} className="relative flex items-start gap-5 group">
              {i !== ALL_PHASES.length - 1 && (
                 <div className={`absolute top-10 left-5 w-px h-[calc(100%-12px)] ${isCompleted ? 'bg-green-500/50 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-[#1E2A45]'} transition-colors duration-500`} />
              )}
              <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 z-10 transition-all duration-300 shadow-sm
                ${isCompleted ? 'bg-green-500/10 text-green-500 border border-green-500/50 shadow-green-900/20' : isCurrent ? 'bg-[#3B82F6]/10 text-blue-400 border border-blue-500 shadow-blue-900/30 ring-4 ring-blue-500/10 animate-pulse' : 'bg-[#141E35] text-slate-600 border border-[#1E2A45]'}
              `}>
                {isCompleted ? <Check className="w-5 h-5" /> : isCurrent ? <Loader2 className="w-5 h-5 animate-spin" /> : <phase.icon className="w-5 h-5" />}
              </div>
              <div className="mt-1">
                 <h4 className={`text-base tracking-wide ${isCompleted ? 'text-slate-200 font-medium' : isCurrent ? 'text-white font-bold' : 'text-slate-500'}`}>{phase.label}</h4>
                 <p className={`text-sm mt-0.5 ${(isCompleted || isCurrent) ? 'text-slate-400' : 'text-slate-600'}`}>{phase.desc}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
