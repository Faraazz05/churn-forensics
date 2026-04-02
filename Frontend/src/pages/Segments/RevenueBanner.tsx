import { DollarSign, AlertCircle } from 'lucide-react'

export function RevenueBanner({ revenueAtRisk, nDegrading }: { revenueAtRisk?: number, nDegrading?: number }) {
  return (
    <div className="bg-gradient-to-r from-red-500/10 to-[#0F1629] border border-red-500/30 p-6 rounded-xl flex items-center justify-between shadow-[0_0_30px_rgba(239,68,68,0.1)] relative overflow-hidden">
      <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
      <div className="flex items-center gap-4 z-10 pl-6">
        <div className="p-3 bg-red-500/20 rounded-full text-red-400 border border-red-500/20 shadow-inner">
          <DollarSign className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-slate-300 text-xs font-bold uppercase tracking-widest mb-1">Total Revenue at Risk</h2>
          <p className="text-3xl font-bold text-white flex items-center gap-3">
            ${((revenueAtRisk || 1250000) / 1000000).toFixed(2)}M
            <span className="text-xs font-bold text-red-400 bg-red-500/10 px-2 py-1 rounded border border-red-500/20 shadow-inner">
              HIGH PRIORITY
            </span>
          </p>
        </div>
      </div>
      <div className="bg-[#141E35]/80 backdrop-blur-sm p-4 rounded-xl border border-red-500/20 flex items-center gap-3 shadow-xl">
        <AlertCircle className="w-6 h-6 text-orange-400" />
        <div>
           <p className="text-sm text-slate-300">Driven largely by <span className="font-bold text-white">{nDegrading || 3} degrading segments</span>.</p>
           <p className="text-xs text-slate-500">Immediate action required.</p>
        </div>
      </div>
    </div>
  )
}
