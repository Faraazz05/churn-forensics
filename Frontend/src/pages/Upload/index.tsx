import { useState } from 'react'
import { DropzoneArea } from './DropzoneArea'
import { ConnectionForm } from './ConnectionForm'
import { SchemaPreview } from './SchemaPreview'

export function UploadData() {
  const [activeTab, setActiveTab] = useState<'upload' | 'db'>('upload')
  const [file, setFile] = useState<File | null>(null)

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Connect Dataset</h1>
        <p className="text-slate-400">Upload a CSV/Excel file or connect directly to your database for real-time risk scoring.</p>
      </div>

      <div className="flex glass-panel p-1 mb-8 w-max">
        <button
          className={`px-6 py-2 rounded-xl font-medium text-sm transition ${activeTab === 'upload' ? 'glass-active text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
          onClick={() => setActiveTab('upload')}
        >
          File Upload
        </button>
        <button
          className={`px-6 py-2 rounded-xl font-medium text-sm transition ${activeTab === 'db' ? 'glass-active text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
          onClick={() => setActiveTab('db')}
        >
          Database Connection
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {activeTab === 'upload' ? (
            <DropzoneArea file={file} setFile={setFile} />
          ) : (
            <ConnectionForm />
          )}
        </div>
        <div className="lg:col-span-1">
          <div className="glass-card p-6 h-full">
            <h3 className="text-lg font-bold text-slate-100 mb-4">Data Requirements</h3>
            <ul className="space-y-4 text-sm text-slate-400">
               <li className="flex gap-2 leading-relaxed"><span className="text-blue-500 text-lg mt-[-2px]">•</span> Must contain a unique Customer ID</li>
               <li className="flex gap-2 leading-relaxed"><span className="text-blue-500 text-lg mt-[-2px]">•</span> Minimum 3 months of historical data</li>
               <li className="flex gap-2 leading-relaxed"><span className="text-blue-500 text-lg mt-[-2px]">•</span> Supported formats: .csv, .xlsx, .xls</li>
               <li className="flex gap-2 leading-relaxed glass-panel p-3 mt-2">
                 <span className="text-purple-500">★</span> Target column (e.g. "churned") is optional for scoring, required for retraining.
               </li>
            </ul>
          </div>
        </div>
      </div>
      
      {file && activeTab === 'upload' && (
        <div className="mt-8">
           <SchemaPreview />
        </div>
      )}
    </div>
  )
}
