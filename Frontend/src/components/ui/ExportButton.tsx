import { useState } from 'react'
import { FileDown, FileText, FileSpreadsheet, Code } from 'lucide-react'
import { useExport } from '../../hooks/useExport'

export function ExportButton() {
  const [isOpen, setIsOpen] = useState(false)
  const { exportPdf, exportExcel } = useExport()

  const handleExport = (type: 'pdf' | 'excel' | 'json') => {
    setIsOpen(false)
    if (type === 'pdf') exportPdf()
    else if (type === 'excel') exportExcel()
    else {
      // For JSON export mock or simple trigger
      alert("JSON export via API triggered.")
    }
  }

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-navy-800 border border-navy-600 rounded-lg text-slate-300 hover:text-white hover:bg-navy-700 transition"
      >
        <FileDown className="w-4 h-4" />
        Export
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-48 bg-navy-800 border border-navy-600 rounded-lg shadow-xl overflow-hidden z-50">
            <button onClick={() => handleExport('pdf')} className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-navy-700 hover:text-white transition">
              <FileText className="w-4 h-4 text-blue-400" /> PDF Report
            </button>
            <button onClick={() => handleExport('excel')} className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-navy-700 hover:text-white border-y border-navy-700 transition">
              <FileSpreadsheet className="w-4 h-4 text-green-400" /> Excel Data
            </button>
            <button onClick={() => handleExport('json')} className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-navy-700 hover:text-white transition">
              <Code className="w-4 h-4 text-purple-400" /> Raw JSON
            </button>
          </div>
        </>
      )}
    </div>
  )
}
