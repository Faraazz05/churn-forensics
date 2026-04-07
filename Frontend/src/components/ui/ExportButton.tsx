import { useState, useRef, useEffect } from 'react'
import { FileDown, FileText, FileSpreadsheet, Code } from 'lucide-react'
import { useExport } from '../../hooks/useExport'

export function ExportButton() {
  const [isOpen, setIsOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const { exportPdf, exportExcel } = useExport()

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [isOpen])

  const handleExport = (type: 'pdf' | 'excel' | 'json') => {
    setIsOpen(false)
    if (type === 'pdf') exportPdf()
    else if (type === 'excel') exportExcel()
    else exportJson()
  }

  const exportJson = async () => {
    try {
      const response = await fetch('/api/insights')
      const data = await response.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `forensics_export_${new Date().getTime()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error("Failed to export JSON", e)
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-5 py-2.5 bg-white/[0.05] border border-white/10 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all duration-300 shadow-sm hover:shadow-[0_0_15px_rgba(59,130,246,0.15)]"
      >
        <FileDown className="w-4 h-4" />
        Export
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-52 bg-[#0F1629] border border-[#1E2A45] rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.4)] overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          <button onClick={() => handleExport('pdf')} className="w-full flex items-center gap-3 px-5 py-3.5 text-sm text-slate-300 hover:bg-white/[0.05] hover:text-white transition-colors">
            <FileText className="w-4 h-4 text-blue-400" /> PDF Report
          </button>
          <div className="border-t border-[#1E2A45]" />
          <button onClick={() => handleExport('excel')} className="w-full flex items-center gap-3 px-5 py-3.5 text-sm text-slate-300 hover:bg-white/[0.05] hover:text-white transition-colors">
            <FileSpreadsheet className="w-4 h-4 text-green-400" /> CSV / Excel Data
          </button>
          <div className="border-t border-[#1E2A45]" />
          <button onClick={() => handleExport('json')} className="w-full flex items-center gap-3 px-5 py-3.5 text-sm text-slate-300 hover:bg-white/[0.05] hover:text-white transition-colors">
            <Code className="w-4 h-4 text-purple-400" /> Raw JSON
          </button>
        </div>
      )}
    </div>
  )
}
