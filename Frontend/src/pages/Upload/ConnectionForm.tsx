import { useState } from 'react'
import { Database, CheckCircle, AlertTriangle } from 'lucide-react'
import { useSystemHealth } from '../../hooks/useSystemHealth'

export function ConnectionForm() {
  const { data: health, refetch, isLoading } = useSystemHealth()
  const [tested, setTested] = useState(false)

  const handleTest = async (e: React.FormEvent) => {
    e.preventDefault()
    await refetch()
    setTested(true)
  }

  return (
    <div className="bg-[#0F1629] border border-[#1E2A45] rounded-xl p-8 shadow-lg h-full min-h-[320px]">
      <div className="flex items-center gap-4 mb-8 pb-6 border-b border-[#1E2A45]">
        <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-xl flex items-center justify-center">
          <Database className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Database Configuration</h2>
          <p className="text-slate-400 mt-1">Connect securely to your data warehouse</p>
        </div>
      </div>

      <form className="space-y-5" onSubmit={handleTest}>
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-4">
            <label className="block text-sm font-medium text-slate-300 mb-1">Host Url</label>
            <input type="text" defaultValue="aws-us-east-1.datawarehouse.internal" className="w-full bg-[#0A0D1A] border border-[#1E2A45] rounded-lg px-4 py-2.5 text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition" />
          </div>
          <div className="col-span-1">
            <label className="block text-sm font-medium text-slate-300 mb-1">Port</label>
            <input type="text" defaultValue="5439" className="w-full bg-[#0A0D1A] border border-[#1E2A45] rounded-lg px-4 py-2.5 text-white focus:border-blue-500 focus:outline-none transition" />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Database Name</label>
          <input type="text" defaultValue="prod_customer_events" className="w-full bg-[#0A0D1A] border border-[#1E2A45] rounded-lg px-4 py-2.5 text-white focus:border-blue-500 focus:outline-none transition" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Service Username</label>
            <input type="text" defaultValue="svc_health_read" className="w-full bg-[#0A0D1A] border border-[#1E2A45] rounded-lg px-4 py-2.5 text-white focus:border-blue-500 focus:outline-none transition" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password / API Key</label>
            <input type="password" defaultValue="********" className="w-full bg-[#0A0D1A] border border-[#1E2A45] rounded-lg px-4 py-2.5 text-slate-400 focus:border-blue-500 focus:outline-none transition" />
          </div>
        </div>

        <div className="pt-6 mt-4 border-t border-[#1E2A45] flex items-center justify-between">
          <div className="flex-1">
            {tested && (
               <div className="flex items-center gap-2">
                 {health?.status === 'ok' ? (
                   <><CheckCircle className="w-5 h-5 text-green-500" /><span className="text-green-400 text-sm font-medium">Connection Successful</span></>
                 ) : (
                   <><AlertTriangle className="w-5 h-5 text-red-500" /><span className="text-red-400 text-sm font-medium">Connection Failed</span></>
                 )}
               </div>
            )}
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={handleTest} disabled={isLoading} className="px-6 py-2 bg-[#1E2A45] text-slate-200 font-medium rounded-lg hover:bg-slate-700 transition disabled:opacity-50">
              {isLoading ? 'Testing...' : 'Test Connection'}
            </button>
            <button type="submit" disabled={!tested || health?.status !== 'ok'} className="px-6 py-2 bg-blue-600 text-white font-medium shadow-lg shadow-blue-900/20 rounded-lg hover:bg-blue-500 transition disabled:opacity-50">
              Connect & Run
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
