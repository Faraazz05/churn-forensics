import { AlertCircle, Wrench, CheckCircle } from 'lucide-react'

export function RetrainingBanner({ trigger }: { trigger?: any }) {
  if (!trigger) return null;
  
  const isRequired = trigger.model_retraining_required;

  return (
    <div className={`p-6 rounded-xl border flex items-center justify-between shadow-xl mb-8 relative overflow-hidden transition-all ${
      isRequired ? 'bg-orange-500/10 border-orange-500/30' : 'bg-[#0F1629] border-[#1E2A45]'
    }`}>
      {isRequired && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.8)]" />}
      
      <div className="flex items-center gap-4 z-10 pl-4">
        <div className={`p-3 rounded-full border shadow-inner ${isRequired ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
          {isRequired ? <Wrench className="w-6 h-6" /> : <CheckCircle className="w-6 h-6" />}
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-widest mb-1 text-slate-400">
             Model Health Status
          </h2>
          <p className="text-2xl font-bold text-white tracking-wide">
            {isRequired ? 'Retraining Required' : 'Model is Stable'}
          </p>
        </div>
      </div>
      
      {isRequired && (
        <div className="bg-[#141E35] p-5 rounded-xl border border-orange-500/20 flex items-center gap-4 shadow-lg">
          <div className="p-2 bg-orange-500/10 rounded-lg">
            <AlertCircle className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">{trigger.reason}</p>
            {trigger.features_above_threshold && (
              <p className="text-xs text-slate-400 mt-1 font-mono">Triggers: {trigger.features_above_threshold.join(', ')}</p>
            )}
          </div>
          <button className="ml-4 px-6 py-2.5 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 text-white rounded-lg font-bold text-xs uppercase transition-all shadow-[0_0_15px_rgba(249,115,22,0.4)]">
            Initiate Pipeline
          </button>
        </div>
      )}
    </div>
  )
}
