import { useEffect, useRef, useState } from 'react'
import { Terminal } from 'lucide-react'

export function SystemLogPanel() {
  const [logs, setLogs] = useState<string[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const defaultLogs = [
      '[INFO] Connecting to warehouse...',
      '[INFO] Established connection (Latency: 42ms)',
      '[INFO] Querying base tables (customer_base_v2)...',
      '[WARN] Null values found in "login_frequency" (0.01% rows)',
      '[INFO] Imputation applied (strategy: median)',
      '[INFO] Feature Pipeline: Started',
      '[INFO] Applying standard scaling on numerical features...',
      '[INFO] Creating rolling averages (window=90d)...',
      '[INFO] AutoML: Grid search initiated over 4 models.',
      '[INFO] AutoML: LogisticRegression AUC=0.892',
      '[INFO] AutoML: XGBoost AUC=0.941',
      '[INFO] Winner selected: XGBoost.',
      '[INFO] SHAP Explainer: calculating base values.',
    ]
    
    let i = 0
    const interval = setInterval(() => {
      if (i < defaultLogs.length) {
        setLogs(prev => [...prev, defaultLogs[i]])
        i++
      }
    }, 1800)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="glass-panel rounded-2xl flex flex-col h-full overflow-hidden shadow-2xl relative">
      <div className="absolute inset-0 bg-blue-900/[0.02] bg-[radial-gradient(circle_at_bottom,_var(--tw-gradient-stops))] from-blue-500/[0.05] via-transparent to-transparent pointer-events-none" />
      <div className="px-5 py-3 bg-black/20 backdrop-blur-md border-b border-white/10 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-mono text-slate-300 tracking-wider">stdout logging</span>
        </div>
        <div className="flex items-center gap-2">
           <div className="w-2.5 h-2.5 rounded-full bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
           <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80 shadow-[0_0_8px_rgba(234,179,8,0.5)]" />
           <div className="w-2.5 h-2.5 rounded-full bg-green-500/80 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
        </div>
      </div>
      <div className="flex-1 p-5 font-mono text-sm overflow-y-auto leading-loose tracking-wide relative z-10 custom-scrollbar">
        {logs.map((log, idx) => (
          <div key={idx} className={`mb-1.5 break-words ${log.includes('WARN') ? 'text-yellow-400 font-medium' : 'text-emerald-400 drop-shadow-sm'}`}>
             <span className="text-slate-500 mr-3 select-none">[{new Date().toISOString().split('T')[1].slice(0,-1)}]</span>
             {log}
          </div>
        ))}
        {logs.length < 13 && (
          <div className="flex items-center gap-2 mt-4 ml-2">
             <div className="w-2 h-4 bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
          </div>
        )}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  )
}
