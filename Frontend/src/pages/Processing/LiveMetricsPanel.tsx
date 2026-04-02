import { Activity, Cpu, HardDrive, Network } from 'lucide-react'

export function LiveMetricsPanel() {
  return (
    <div className="bg-[#0F1629] p-6 rounded-xl border border-[#1E2A45] shadow-[0_0_30px_rgba(0,0,0,0.5)] relative overflow-hidden group hover:border-[#1E2A45]/80 transition-all h-full">
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
      
      <div className="flex items-center gap-3 mb-6 pb-3 border-b border-[#1E2A45]">
         <div className="relative">
           <Activity className="w-5 h-5 text-emerald-400 z-10 relative" />
           <div className="absolute inset-0 bg-emerald-400 blur-sm opacity-50 animate-pulse"></div>
         </div>
         <h2 className="text-lg font-bold text-white tracking-wide">Live Telemetry</h2>
      </div>

      <div className="grid grid-cols-2 gap-4">
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] relative overflow-hidden">
           <Cpu className="w-8 h-8 text-white/5 absolute -right-2 -bottom-2" />
           <p className="text-slate-400 text-xs mb-1 flex justify-between">CPU Load <span className="text-emerald-400">Stable</span></p>
           <p className="text-white font-mono text-2xl group-hover:text-emerald-300 transition-colors">42%</p>
         </div>
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] relative overflow-hidden">
           <HardDrive className="w-8 h-8 text-white/5 absolute -right-2 -bottom-2" />
           <p className="text-slate-400 text-xs mb-1">RAM Usage</p>
           <p className="text-white font-mono text-2xl">1.2<span className="text-sm text-slate-500">GB</span></p>
         </div>
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] relative overflow-hidden">
           <Network className="w-8 h-8 text-white/5 absolute -right-2 -bottom-2" />
           <p className="text-slate-400 text-xs mb-1">Throughput</p>
           <p className="text-white font-mono text-2xl">8.4k<span className="text-sm text-slate-500"> /s</span></p>
         </div>
         <div className="bg-[#141E35] p-4 rounded-xl border border-[#1E2A45] relative overflow-hidden">
           <p className="text-slate-400 text-xs mb-1">Allocated Node</p>
           <div className="mt-2 flex items-center gap-2">
             <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)] animate-pulse"></span>
             <p className="text-emerald-400 font-mono text-sm leading-tight text-wrap">ml.c5.xlarge</p>
           </div>
         </div>
      </div>
    </div>
  )
}
