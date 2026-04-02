import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, X } from 'lucide-react'
import { useEffect } from 'react'

export interface ToastProps {
  id?: string
  type: 'success' | 'error'
  message: string
  onClose?: () => void
}

export function Toast({ type, message, onClose }: ToastProps) {
  useEffect(() => {
    if (onClose) {
      const timer = setTimeout(onClose, 5000)
      return () => clearTimeout(timer)
    }
  }, [onClose])

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-green-500" />,
    error: <XCircle className="w-5 h-5 text-red-500" />
  }

  const bgs = {
    success: 'bg-[#071A12] border-green-900',
    error: 'bg-[#1F0A0A] border-red-900'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      className={`fixed bottom-4 right-4 flex items-center gap-3 p-4 border rounded-xl shadow-2xl z-50 min-w-[300px] ${bgs[type]}`}
    >
      {icons[type]}
      <p className="flex-1 text-sm font-medium text-slate-200">{message}</p>
      {onClose && (
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-md transition-colors">
          <X className="w-4 h-4 text-slate-400" />
        </button>
      )}
    </motion.div>
  )
}
