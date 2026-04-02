import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { useSystemHealth } from '../../hooks/useSystemHealth'

export function DemoEntry() {
  const navigate = useNavigate()
  const { data: health, isLoading } = useSystemHealth()

  useEffect(() => {
    if (health?.status === 'ok') {
      const timer = setTimeout(() => {
        navigate('/demo/model')
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [health, navigate])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center">
      <div className="max-w-md w-full p-8 rounded-2xl border border-[#1E2A45] bg-[#0F1629] shadow-2xl relative overflow-hidden">
         <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
         <h1 className="text-2xl font-bold text-white mb-2 pt-4">Initializing System</h1>
         <p className="text-slate-400 mb-8">Connecting to Customer Health Backend...</p>
         
         {isLoading ? (
           <LoadingSpinner message="Checking system health..." />
         ) : health?.status === 'ok' ? (
           <div className="flex flex-col items-center gap-2">
             <div className="w-12 h-12 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mb-2">
               <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
               </svg>
             </div>
             <span className="text-green-400 font-medium">Connection Established</span>
             <span className="text-slate-500 text-sm mb-4">Loading 500K customer records...</span>
           </div>
         ) : (
           <div className="text-red-400 font-medium p-6 bg-red-950/20 rounded-lg border border-red-900/50">
             Backend Offline. Please ensure FastAPI is running on port 3000.
           </div>
         )}
      </div>
    </div>
  )
}
