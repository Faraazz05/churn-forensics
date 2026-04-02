import { Loader2 } from 'lucide-react'

export function LoadingSpinner({ message = "Loading...", className = "" }: { message?: string, className?: string }) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 space-y-4 ${className}`}>
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      <span className="text-slate-400 text-sm">{message}</span>
    </div>
  )
}
