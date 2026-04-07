import { useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'

export function StepperNavigation() {
  const { pathname } = useLocation()
  const navigate = useNavigate()

  const isDemo = pathname.startsWith('/demo')
  const prefix = isDemo ? '/demo' : '/analysis'
  
  const steps = [
    { path: '/upload', label: 'Input Data' },
    { path: 'processing', label: 'Processing' },
    { path: `${prefix}/model`, label: 'Model + XAI' },
    { path: `${prefix}/dashboard`, label: 'Dashboard Analysis' }
  ]

  let currentIndex = -1
  if (pathname === '/upload') currentIndex = 0
  else if (pathname.includes('/processing')) currentIndex = 1
  else if (pathname === `${prefix}/model`) currentIndex = 2
  else if (pathname === `${prefix}/dashboard`) currentIndex = 3

  if (currentIndex === -1 || currentIndex === 1) return null

  const handlePrev = () => {
    if (currentIndex > 0) {
      if (currentIndex === 2) navigate(isDemo ? '/' : '/upload') // skip processing going back
      else navigate(steps[currentIndex - 1].path)
    }
  }

  const handleNext = () => {
    if (currentIndex < steps.length - 1) {
       navigate(steps[currentIndex + 1].path)
    }
  }

  const isUpload = currentIndex === 0;
  const isEnd = currentIndex === steps.length - 1;

  return (
    <div className="fixed bottom-0 left-0 right-0 h-[72px] bg-white/5 dark:bg-black/20 backdrop-blur-xl border-t border-white/10 flex items-center justify-between px-8 z-40 transition-all duration-300">
      <button 
        onClick={handlePrev}
        disabled={isUpload}
        className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-all duration-300 ${isUpload ? 'opacity-0 cursor-default' : 'text-slate-200 hover:text-white hover:bg-white/10 border border-white/10 shadow-sm hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]'}`}
      >
        <ArrowLeft className="w-4 h-4" /> Previous
      </button>

      <div className="flex items-center gap-6">
         {steps.map((step, idx) => (
            <div key={idx} className="flex flex-col items-center gap-1.5 cursor-default">
              <div className={`w-10 h-1 rounded-full transition-all duration-500 ${idx === currentIndex ? 'bg-blue-400 shadow-[0_0_15px_rgba(96,165,250,0.8)]' : idx < currentIndex ? 'bg-blue-500/40' : 'bg-white/5'}`} />
              <span className={`text-[10px] font-bold tracking-wider uppercase transition-colors duration-300 ${idx === currentIndex ? 'text-blue-300' : idx < currentIndex ? 'text-blue-500/50' : 'text-slate-600'}`}>
                {step.label}
              </span>
            </div>
         ))}
      </div>

      <button
        onClick={handleNext}
        disabled={isUpload || isEnd} 
        className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-all duration-300 ${isUpload || isEnd ? 'opacity-0 cursor-default' : 'text-white bg-blue-600/80 hover:bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)] border border-blue-400/50 hover:shadow-[0_0_25px_rgba(59,130,246,0.6)]'}`}
      >
        Next Step <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  )
}
