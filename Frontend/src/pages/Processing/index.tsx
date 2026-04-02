import { useParams, useNavigate } from 'react-router-dom'
import { usePipelineStatus } from '../../hooks/usePipeline'
import { PipelineStageTracker } from './PipelineStageTracker'
import { SystemLogPanel } from './SystemLogPanel'
import { LiveMetricsPanel } from './LiveMetricsPanel'

export function Processing() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const { data: statusData } = usePipelineStatus(runId || '')

  const isDone = statusData?.status === 'done'

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex items-center justify-between mb-8 pb-8 border-b border-white/10">
        <div>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-3 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]">System Processing</h1>
          <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-xl border ${!isDone ? 'bg-blue-500/10 border-blue-500/30 animate-pulse' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
            <span className="text-xl">{!isDone ? '⚙️' : '✅'}</span>
            <p className={`text-lg font-medium tracking-wide ${!isDone ? 'text-blue-300' : 'text-emerald-400'}`}>
              {!isDone ? "Training and evaluating ML algorithms on latest dataset..." : "Analysis complete. Models are ready."} 
              <span className="ml-3 font-mono text-sm opacity-50">[{runId}]</span>
            </p>
          </div>
        </div>
        {isDone ? (
          <button onClick={() => navigate('/analysis/model')} className="px-6 py-3 bg-blue-600/80 text-white font-medium rounded-xl hover:bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all flex items-center gap-2 border border-blue-400/50">
            View Final Results <span aria-hidden="true">&rarr;</span>
          </button>
        ) : (
          <div className="flex items-center gap-3 px-5 py-2.5 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <div className="w-5 h-5 rounded-full border-2 border-current border-t-transparent animate-spin" />
            <span className="font-bold tracking-wider text-sm">PIPELINE ACTIVE</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 min-h-[600px]">
         <div className="lg:col-span-2 flex flex-col gap-8 h-full">
           <div className="flex-none">
             <LiveMetricsPanel />
           </div>
           <div className="flex-1">
             <PipelineStageTracker phases={statusData?.phases_run || []} isDone={isDone} />
           </div>
         </div>
         <div className="lg:col-span-1 h-full">
           <SystemLogPanel />
         </div>
      </div>
    </div>
  )
}
