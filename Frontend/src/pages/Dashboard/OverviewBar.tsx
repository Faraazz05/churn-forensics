import { MetricCard } from '../../components/ui/MetricCard'
import { InsightResponse } from '../../types/api'

interface OverviewBarProps {
  insights?: InsightResponse
  segmentData?: any
}

export function OverviewBar({ insights, segmentData }: OverviewBarProps) {
  const rAtRisk = insights?.business_impact?.total_annual_revenue_at_risk || 0
  const criticallyAtRisk = insights?.business_impact?.critical_customers_count || 0
  const degradingCount = segmentData?.global_insights?.n_degrading || 0
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
       <MetricCard label="Total Revenue at Risk" value={rAtRisk} format="currency" change={0} />
       <MetricCard label="Global Churn Rate" value={0} format="percent" change={0} />
       <MetricCard label="Critical Risk Customers" value={criticallyAtRisk} format="number" change={0} />
       <MetricCard label="Segments Degrading" value={degradingCount} format="number" change={0} />
    </div>
  )
}
