import { DivideIcon as LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: typeof LucideIcon
  title: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon: Icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="w-full p-12 border border-navy-600 bg-navy-800/50 rounded-xl flex flex-col items-center justify-center text-center">
      <div className="p-4 bg-navy-700 rounded-full mb-4">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-200 mb-2">{title}</h3>
      <p className="text-slate-400 max-w-sm mb-6">{message}</p>
      {action && (
        <button 
          onClick={action.onClick}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-500 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
