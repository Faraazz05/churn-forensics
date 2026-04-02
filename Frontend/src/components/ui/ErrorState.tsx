import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="w-full p-8 border border-red-900/50 bg-red-950/20 rounded-xl flex flex-col items-center justify-center text-center">
      <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
      <h3 className="text-lg font-semibold text-red-400 mb-2">Failed to load data</h3>
      <p className="text-slate-400 max-w-md">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="mt-6 px-4 py-2 bg-red-900/50 text-red-200 border border-red-700/50 rounded-lg hover:bg-red-800/50 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}
