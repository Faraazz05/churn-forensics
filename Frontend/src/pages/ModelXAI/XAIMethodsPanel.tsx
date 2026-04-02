import { Fingerprint, Brain, Activity } from 'lucide-react'

export function XAIMethodsPanel() {
  const methods = [
    { name: 'SHAP TreeExplainer', role: 'Primary Method', icon: Fingerprint, desc: 'Exact, fast, native tree support for boosting architectures computing precise marginal contributions.', color: 'blue' },
    { name: 'LIME', role: 'Validator', icon: Activity, desc: 'Local surrogate model to double check and map complex nonlinear decision boundary approximations.', color: 'purple' },
    { name: 'AIX360', role: 'Validator', icon: Brain, desc: 'IBM independent attribution check providing contrastive and robust rule-based logic tests.', color: 'emerald' },
  ]

  const colorStyles = {
    blue: 'border-blue-500/20 hover:border-blue-500/50 text-blue-400 bg-blue-500/5',
    purple: 'border-purple-500/20 hover:border-purple-500/50 text-purple-400 bg-purple-500/5',
    emerald: 'border-emerald-500/20 hover:border-emerald-500/50 text-emerald-400 bg-emerald-500/5',
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {methods.map((method) => {
         const theme = colorStyles[method.color as keyof typeof colorStyles];
         return (
          <div key={method.name} className={`bg-[#0F1629] p-8 rounded-xl border shadow-lg relative overflow-hidden group transition-all duration-300 hover:-translate-y-1 ${theme.split(' ')[0]} ${theme.split(' ')[1]}`}>
             <div className={`absolute top-0 right-0 w-32 h-32 rounded-bl-[120px] -z-0 opacity-50 ${theme.split(' ')[3]}`} />
             <method.icon className={`w-10 h-10 mb-5 relative z-10 ${theme.split(' ')[2]}`} />
             <div className={`text-[11px] font-bold tracking-widest uppercase mb-2 relative z-10 ${method.role === 'Primary Method' ? 'text-blue-400' : 'text-slate-500'}`}>
               {method.role}
             </div>
             <h3 className="text-xl font-bold text-white mb-3 relative z-10">{method.name}</h3>
             <p className="text-sm text-slate-400 leading-relaxed relative z-10">{method.desc}</p>
          </div>
        )
      })}
    </div>
  )
}
