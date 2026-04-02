import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, File as FileIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useUpload } from '../../hooks/useUpload'

interface DropzoneProps {
  file: File | null
  setFile: (f: File | null) => void
}

export function DropzoneArea({ file, setFile }: DropzoneProps) {
  const navigate = useNavigate()
  const uploadMutation = useUpload()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0])
  }, [setFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1
  })

  const handleUpload = () => {
    if (!file) return
    uploadMutation.mutate(file, {
      onSuccess: (data) => {
         navigate(`/processing/${data.job_id || 'run_latest'}`)
      }
    })
  }

  if (file) {
    return (
      <div className="glass-panel rounded-2xl p-10 flex flex-col items-center justify-center text-center shadow-[0_8px_32px_rgba(30,58,138,0.2)] h-full min-h-[320px]">
        <div className="p-5 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6 shadow-[0_0_20px_rgba(59,130,246,0.15)]">
          <FileIcon className="w-12 h-12 text-blue-400 drop-shadow-lg" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">{file.name}</h3>
        <p className="text-blue-200/60 mb-8 font-medium">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready for processing</p>
        <div className="flex gap-4">
          <button onClick={() => setFile(null)} className="px-6 py-3 bg-white/5 border border-white/10 text-slate-300 font-medium rounded-xl hover:bg-white/10 hover:text-white transition-all shadow-sm">
            Remove File
          </button>
          <button onClick={handleUpload} disabled={uploadMutation.isPending} className="px-8 py-3 bg-blue-600/90 hover:bg-blue-500 text-white font-medium rounded-xl shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all disabled:opacity-50 disabled:shadow-none border border-blue-400/50">
            {uploadMutation.isPending ? 'Starting...' : 'Start Pipeline'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div {...getRootProps()} className={`glass-panel border-2 border-dashed ${isDragActive ? 'border-blue-400 bg-blue-500/10 shadow-[0_0_30px_rgba(59,130,246,0.15)]' : 'border-white/10 hover:border-blue-500/50 hover:bg-white/5 hover:shadow-[0_0_20px_rgba(59,130,246,0.1)]'} rounded-2xl p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 h-full min-h-[320px] group`}>
      <input {...getInputProps()} />
      <div className={`p-5 rounded-full mb-6 transition-all duration-300 ${isDragActive ? 'bg-blue-500/20 text-blue-400 scale-110 shadow-[0_0_20px_rgba(59,130,246,0.3)]' : 'bg-white/5 text-slate-400 group-hover:bg-blue-500/10 group-hover:text-blue-400 group-hover:scale-105'}`}>
        <UploadCloud className="w-10 h-10" />
      </div>
      <p className="text-xl font-bold text-white mb-3">Drag & drop your dataset</p>
      <p className="text-slate-400 mb-8 max-w-sm font-medium">Use standard formats or export formats from your previous BI tools</p>
      <div className="px-8 py-3 bg-white/10 hover:bg-white/20 border border-white/10 text-white rounded-xl font-medium shadow-lg transition-all">
        Browse Files
      </div>
    </div>
  )
}
