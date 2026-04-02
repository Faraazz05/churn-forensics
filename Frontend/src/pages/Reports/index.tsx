import { FileText, FileSpreadsheet } from 'lucide-react'
import { useExport } from '../../hooks/useExport'

export function ReportsPage() {
  const { exportPdf, exportExcel } = useExport()
  
  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-white mb-8">Report Generation & Export</h1>
      <div className="grid grid-cols-2 gap-8">
         <div onClick={exportPdf} className="bg-[#0F1629] p-10 rounded-xl border border-[#1E2A45] hover:border-blue-500 cursor-pointer shadow-xl flex flex-col items-center justify-center gap-6 transition-all duration-300 group hover:-translate-y-1">
            <FileText className="w-20 h-20 text-slate-500 group-hover:text-blue-500 transition-colors" />
            <div className="text-center">
               <h2 className="text-xl font-bold text-white mb-2">Executive Overview Report</h2>
               <p className="text-sm text-slate-400">PDF formatted summary of all intelligence triggers.</p>
            </div>
         </div>
         <div onClick={exportExcel} className="bg-[#0F1629] p-10 rounded-xl border border-[#1E2A45] hover:border-emerald-500 cursor-pointer shadow-xl flex flex-col items-center justify-center gap-6 transition-all duration-300 group hover:-translate-y-1">
            <FileSpreadsheet className="w-20 h-20 text-slate-500 group-hover:text-emerald-500 transition-colors" />
            <div className="text-center">
               <h2 className="text-xl font-bold text-white mb-2">Full Database Export</h2>
               <p className="text-sm text-slate-400">Excel format containing 500k raw scoring outputs.</p>
            </div>
         </div>
      </div>
    </div>
  )
}
