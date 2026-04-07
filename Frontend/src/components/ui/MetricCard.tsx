import { useEffect, useState } from 'react'
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react'

interface MetricCardProps {
  label: string
  value: number
  change?: number
  format?: 'currency' | 'percent' | 'number'
}

export function MetricCard({ label, value, change, format = 'number' }: MetricCardProps) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    let startTime: number
    const duration = 1000
    
    const animate = (time: number) => {
      if (!startTime) startTime = time
      const progress = Math.min((time - startTime) / duration, 1)
      const easeOutExpo = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
      
      setDisplayValue(value * easeOutExpo)
      
      if (progress < 1) requestAnimationFrame(animate)
    }
    
    requestAnimationFrame(animate)
  }, [value])

  const formattedValue = format === 'currency' 
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(displayValue)
    : format === 'percent'
    ? `${displayValue.toFixed(1)}%`
    : Math.floor(displayValue).toLocaleString()

  return (
    <div className="glass-card p-6 relative overflow-hidden group flex flex-col justify-between h-full hover:shadow-[0_4px_24px_rgba(59,130,246,0.15)] transition-all duration-300">
      <div className="absolute inset-0 bg-blue-500/[0.02] opacity-0 group-hover:opacity-100 transition duration-500 pointer-events-none" />
      <h3 className="text-slate-400 text-sm font-bold tracking-wider uppercase mb-3 relative z-10">{label}</h3>
      <div className="flex items-center justify-between gap-3 relative z-10 w-full overflow-hidden">
        <span className="text-2xl 2xl:text-3xl font-bold font-mono text-white truncate">{formattedValue}</span>
        {change !== undefined && (
          <div className={`flex items-center justify-center shrink-0 min-w-[75px] text-sm font-semibold px-2 py-1.5 rounded-lg border ${change >= 0 ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-red-400 bg-red-500/10 border-red-500/20'}`}>
            {change >= 0 ? <ArrowUpIcon className="w-3.5 h-3.5 mr-1 shrink-0" /> : <ArrowDownIcon className="w-3.5 h-3.5 mr-1 shrink-0" />}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
    </div>
  )
}
