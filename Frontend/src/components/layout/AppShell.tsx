import { Outlet } from 'react-router-dom'
import { TopBar } from './TopBar'
import { StepperNavigation } from './StepperNavigation'

export function AppShell() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0D1A] to-[#0D1224] flex flex-col font-sans">
      <TopBar />
      <main className="flex-1 mt-[56px] mb-[72px] p-8 overflow-y-auto scroll-smooth text-slate-50 relative z-10">
        <div className="absolute inset-0 bg-blue-500/[0.02] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-500/[0.05] via-transparent to-transparent pointer-events-none" />
        <Outlet />
      </main>
      <StepperNavigation />
    </div>
  )
}
