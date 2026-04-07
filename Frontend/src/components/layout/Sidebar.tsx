import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, PieChart, TrendingDown, Lightbulb, Brain, Upload, FileText, Hexagon } from 'lucide-react'
import { useSystemHealth } from '../../hooks/useSystemHealth'

export function Sidebar() {
  const { pathname } = useLocation()
  const { data: health } = useSystemHealth()

  const prefix = '/analysis'
  const navItems = [
    { name: 'Overview', path: `${prefix}/dashboard`, icon: LayoutDashboard },
    { name: 'Watchlist', path: `/analysis/dashboard`, icon: Users }, 
    { name: 'Segments', path: '/segments', icon: PieChart },
    { name: 'Drift', path: '/drift', icon: TrendingDown },
    { name: 'Insights', path: '/insights', icon: Lightbulb },
    { name: 'Model + XAI', path: `${prefix}/model`, icon: Brain },
    { name: 'Upload Data', path: '/upload', icon: Upload },
    { name: 'Reports', path: '/reports', icon: FileText },
  ]

  return (
    <div className="w-[240px] h-screen fixed left-0 top-0 bg-[#0A0D1A] border-r border-[#1E2A45] flex flex-col z-40 bg-opacity-95 backdrop-blur-sm">
      <div className="p-6">
        <Link to="/" className="flex items-center gap-2 mb-6 cursor-pointer">
          <Hexagon className="w-8 h-8 text-blue-500 fill-blue-500/20" />
          <span className="font-bold text-lg text-white">Forensics</span>
        </Link>
        
        <div className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider w-max mb-8 border bg-purple-900/40 text-purple-400 border-purple-800`}>
          LIVE ANALYSIS
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path) && item.name !== 'Watchlist');
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors ${
                isActive
                  ? 'bg-[#1E2A45] text-white border-l-4 border-blue-500' 
                  : 'text-slate-400 hover:bg-[#141E35] hover:text-slate-200 border-l-4 border-transparent'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span className="truncate text-sm">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 mt-auto border-t border-[#1E2A45] flex items-center gap-3">
        <div className="relative flex h-3 w-3">
          {health?.status === 'ok' && (
             <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-3 w-3 ${health?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`}></span>
        </div>
        <div className="text-xs text-slate-400">
           System {health?.status === 'ok' ? 'Operational' : 'Waiting...'}
        </div>
      </div>
    </div>
  )
}
