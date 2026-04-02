import { useParams } from 'react-router-dom'
import { useCustomer } from '../../hooks/useCustomers'
import { RiskBadge } from '../../components/ui/RiskBadge'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { PredictionCard } from './PredictionCard'
import { ExplanationPanel } from './ExplanationPanel'
import { FeatureImportanceChart } from './FeatureImportanceChart'
import { SegmentMembership } from './SegmentMembership'
import { ActionCard } from './ActionCard'

export function CustomerProfile() {
  const { id } = useParams()
  const { data: customer, isLoading } = useCustomer(id || '')

  if (isLoading) return <LoadingSpinner message="Loading customer profile context..." className="min-h-[500px]" />

  return (
    <div className="max-w-7xl mx-auto py-8">
       <div className="bg-gradient-to-r from-[#0F1629] to-[#141E35] p-8 rounded-xl border border-[#1E2A45] mb-8 flex justify-between items-start shadow-xl relative overflow-hidden">
          <div className="z-10 relative">
            <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">{id}</h1>
            <p className="text-slate-400 font-medium">Enterprise Context • Active Since Jan 2023</p>
          </div>
          <div className="z-10 relative mt-2">
             <RiskBadge tier={customer?.prediction?.risk_tier || 'Medium'} />
          </div>
       </div>
       
       <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-1 space-y-8">
             <PredictionCard prediction={customer?.prediction} />
             <SegmentMembership segment={customer?.segment} />
          </div>
          <div className="lg:col-span-2 space-y-8">
             <ActionCard customerId={id || ''} insights={customer?.insights} />
             <ExplanationPanel explanation={customer?.explanation} />
             <FeatureImportanceChart explanations={customer?.explanation?.explanations} />
          </div>
       </div>
    </div>
  )
}
