import { TrendingDown, AlertTriangle } from 'lucide-react'

export function DegradationBadge({ status, delta }: { status?: string, delta?: number }) {
  if (status !== 'degrading' && (!delta || delta < 0.02)) return null;
  
  const isCritical = delta && delta > 0.05;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-bold shadow-inner border ${
      isCritical ? 'bg-red-500/20 border-red-500/40 text-red-400' : 'bg-orange-500/10 border-orange-500/30 text-orange-400'
    }`}>
       {isCritical ? <AlertTriangle className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
       {isCritical ? 'CRITICAL RISK' : 'DEGRADING'}
       {delta && <span className="ml-1 opacity-80">(+{(delta * 100).toFixed(1)}%)</span>}
    </div>
  )
}
