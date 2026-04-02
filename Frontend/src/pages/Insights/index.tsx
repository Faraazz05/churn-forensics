import { useState } from 'react'
import { useInsightsData, useAgentQA } from '../../hooks/useInsights'
import { CausalChainView } from './CausalChainView'
import { BusinessImpactPanel } from './BusinessImpactPanel'
import { Bot } from 'lucide-react'

export function InsightsPage() {
  const { data } = useInsightsData()
  const agent = useAgentQA()
  const [q, setQ] = useState('')
  const [ans, setAns] = useState<string | null>(null)

  const ask = () => {
    if (!q) return;
    agent.mutate(q, { onSuccess: (res) => setAns(res.answer) })
  }

  return (
    <div className="max-w-7xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Conversational Intelligence</h1>
        <p className="text-slate-400 text-lg">Deep dive into causes, impact, and AI-driven analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8 flex flex-col">
          <div className="bg-[#0F1629] p-8 rounded-xl border border-[#1E2A45] shadow-xl flex-1 flex flex-col">
             <div className="flex items-center gap-3 mb-6 border-b border-[#1E2A45] pb-4">
                <div className="p-2.5 bg-blue-500/20 rounded-xl shadow-inner border border-blue-500/30">
                   <Bot className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-xl font-bold text-white tracking-wide">Ask anything about the cohort risk drivers</h2>
             </div>

             <div className="flex flex-col gap-4 flex-1">
               <input 
                 value={q} 
                 onChange={e => setQ(e.target.value)} 
                 onKeyDown={e => e.key === 'Enter' && ask()}
                 placeholder="e.g. Why are NA Enterprise users churning more this quarter?" 
                 className="w-full bg-[#0A0D1A] border border-[#1E2A45] text-white p-5 rounded-lg focus:border-blue-500 outline-none transition-colors shadow-inner"
               />
               <div className="flex justify-end">
                 <button onClick={ask} disabled={agent.isPending || !q} className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white font-bold rounded-lg disabled:opacity-50 hover:from-blue-500 hover:to-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all flex items-center gap-2">
                   {agent.isPending ? (
                     <>
                        <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                        Analyzing...
                     </>
                   ) : 'Execute Query'}
                 </button>
               </div>
               
               {ans && (
                 <div className="mt-8 p-6 bg-[#141E35] border border-blue-500/30 rounded-xl text-blue-100 leading-relaxed shadow-lg relative overflow-hidden">
                   <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                   <p className="whitespace-pre-wrap">{ans}</p>
                 </div>
               )}
             </div>
          </div>
          
          <CausalChainView data={data?.causal_analysis} />
        </div>

        <div className="lg:col-span-1 space-y-8">
          <BusinessImpactPanel impact={data?.business_impact} />
        </div>
      </div>
    </div>
  )
}
