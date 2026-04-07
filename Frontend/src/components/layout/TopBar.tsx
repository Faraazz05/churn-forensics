import { useLocation } from 'react-router-dom'

export function TopBar() {
  const { pathname } = useLocation()

  // Simple string capitalization for breadcrumb mapping
  const breadcrumb = pathname === '/upload' ? 'Upload Dataset' :
                     pathname.includes('/processing') ? 'System Processing' :
                     pathname.includes('/model') ? 'Model & XAI' :
                     pathname.includes('/dashboard') ? 'Executive Dashboard' :
                     pathname.split('/').filter(Boolean).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' / ') || 'Home'

  return (
    <header className="fixed top-0 left-0 right-0 h-[56px] bg-[#0A0D1A]/60 backdrop-blur-xl border-b border-white/10 flex items-center justify-between px-8 z-30 transition-all duration-300">
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-100 to-slate-400">
          Forensics <span className="text-slate-600 font-normal ml-2">|</span> <span className="ml-2 text-sm font-medium text-slate-300">{breadcrumb}</span>
        </div>
      </div>
      

    </header>
  )
}
