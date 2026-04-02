import { ConfidenceLevel } from '../../types/api'

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const settings = {
    HIGH: { color: 'text-green-500', label: '✓ HIGH' },
    MEDIUM: { color: 'text-yellow-500', label: '~ MEDIUM' },
    LOW: { color: 'text-red-500', label: '✗ LOW' },
  }
  const { color, label } = settings[level]
  return <span className={`text-xs font-bold ${color}`}>{label}</span>
}
