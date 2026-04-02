import { RiskTier } from '../../types/api'

export function RiskBadge({ tier }: { tier: RiskTier }) {
  const styles = {
    Critical: 'bg-[#1F0A0A] text-[#EF4444] border border-[#EF4444]',
    High: 'bg-[#1F1505] text-[#F59E0B] border border-[#F59E0B]',
    Medium: 'bg-[#0A0F1F] text-[#3B82F6] border border-[#3B82F6]',
    Safe: 'bg-[#071A12] text-[#10B981] border border-[#10B981]',
  }
  return (
    <span className={`px-3 py-1 text-[11px] font-bold uppercase rounded-full ${styles[tier]}`}>
      {tier}
    </span>
  )
}
