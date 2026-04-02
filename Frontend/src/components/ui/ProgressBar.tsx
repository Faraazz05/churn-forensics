import { motion } from 'framer-motion'

export function ProgressBar({ progress, colorClass = "bg-blue-500", className = "" }: { progress: number, colorClass?: string, className?: string }) {
  return (
    <div className={`w-full bg-navy-700 rounded-full h-2 overflow-hidden ${className}`}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        transition={{ duration: 1, ease: 'easeOut' }}
        className={`h-full ${colorClass}`}
      />
    </div>
  )
}
