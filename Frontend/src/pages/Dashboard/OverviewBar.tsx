import { MetricCard } from '../../components/ui/MetricCard'
import { InsightResponse } from '../../types/api'

export function OverviewBar({ insights }: { insights?: InsightResponse }) {
  const rAtRisk = insights?.business_impact?.total_annual_revenue_at_risk || 4200000
  const criticallyAtRisk = insights?.business_impact?.critical_customers_count || 120
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
       <MetricCard label="Total Revenue at Risk" value={rAtRisk} format="currency" change={12.4} />
       <MetricCard label="Global Churn Rate" value={18.2} format="percent" change={-2.1} />
       <MetricCard label="Critical Risk Customers" value={criticallyAtRisk} format="number" change={5.0} />
       <MetricCard label="Segments Degrading" value={3} format="number" change={0} />
    </div>
  )
}
