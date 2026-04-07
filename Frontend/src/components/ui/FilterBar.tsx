import { useState, useRef, useEffect } from 'react'
import { Search, Filter, ChevronDown, X, Users, AlertTriangle, Calendar, Hash, SlidersHorizontal } from 'lucide-react'

export type FilterPreset = 'all' | 'last_200' | 'month' | 'customer_id' | 'top_critical' | 'risk_tier' | 'region' | 'plan'

export interface DashboardFilters {
  preset: FilterPreset
  customerId?: string
  topN?: number
  riskTier?: string
  region?: string
  plan?: string
  month?: string
}

interface FilterBarProps {
  filters: DashboardFilters
  onChange: (filters: DashboardFilters) => void
  totalCustomers: number
  filteredCount: number
}

const PRESETS: { id: FilterPreset; label: string; icon: any; description: string }[] = [
  { id: 'all', label: 'All Customers', icon: Users, description: 'View entire customer base' },
  { id: 'last_200', label: 'Last 200', icon: Hash, description: 'Most recently scored 200 customers' },
  { id: 'top_critical', label: 'Top Critical', icon: AlertTriangle, description: 'Most likely to churn' },
  { id: 'month', label: 'Month-wise', icon: Calendar, description: 'Filter by scoring month' },
  { id: 'customer_id', label: 'By Customer ID', icon: Search, description: 'Search specific customer' },
  { id: 'risk_tier', label: 'By Risk Tier', icon: SlidersHorizontal, description: 'Filter by risk category' },
  { id: 'region', label: 'By Region', icon: Filter, description: 'Filter by geography' },
  { id: 'plan', label: 'By Plan', icon: Filter, description: 'Filter by contract plan' },
]

const TOP_N_OPTIONS = [50, 100, 200, 500]
const RISK_TIERS = ['Critical', 'High', 'Medium', 'Safe']
const REGIONS = ['US-East', 'US-West', 'EMEA', 'APAC', 'LATAM']
const PLANS = ['Enterprise', 'Professional', 'Starter', 'Basic', 'Growth', 'Team']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function FilterBar({ filters, onChange, totalCustomers, filteredCount }: FilterBarProps) {
  const [showPresets, setShowPresets] = useState(false)
  const presetsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (presetsRef.current && !presetsRef.current.contains(e.target as Node)) {
        setShowPresets(false)
      }
    }
    if (showPresets) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showPresets])

  const activePreset = PRESETS.find(p => p.id === filters.preset)
  const ActiveIcon = activePreset?.icon || Filter

  const updatePreset = (preset: FilterPreset) => {
    const newFilters: DashboardFilters = { preset }
    if (preset === 'top_critical') newFilters.topN = 100
    onChange(newFilters)
    setShowPresets(false)
  }

  const clearFilters = () => {
    onChange({ preset: 'all' })
  }

  return (
    <div className="glass-card p-4 flex flex-wrap items-center gap-3 relative z-30">
      {/* Preset selector dropdown */}
      <div className="relative" ref={presetsRef}>
        <button
          onClick={() => setShowPresets(!showPresets)}
          className="flex items-center gap-2.5 px-4 py-2.5 bg-blue-500/10 border border-blue-500/30 rounded-xl text-sm font-medium text-blue-300 hover:bg-blue-500/20 transition-all min-w-[200px]"
        >
          <ActiveIcon className="w-4 h-4" />
          <span>{activePreset?.label || 'All Customers'}</span>
          <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${showPresets ? 'rotate-180' : ''}`} />
        </button>

        {showPresets && (
          <div className="absolute left-0 mt-2 w-72 bg-[#0F1629] border border-[#1E2A45] rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
            {PRESETS.map(preset => {
              const Icon = preset.icon
              return (
                <button
                  key={preset.id}
                  onClick={() => updatePreset(preset.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                    filters.preset === preset.id
                      ? 'bg-blue-500/10 text-blue-300 border-l-2 border-blue-500'
                      : 'text-slate-300 hover:bg-white/5 border-l-2 border-transparent'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">{preset.label}</p>
                    <p className="text-xs text-slate-500">{preset.description}</p>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Secondary controls based on active preset */}
      {filters.preset === 'customer_id' && (
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={filters.customerId || ''}
            onChange={(e) => onChange({ ...filters, customerId: e.target.value })}
            placeholder="CUST_0123456..."
            className="w-full pl-10 pr-4 py-2.5 bg-[#141E35] border border-[#1E2A45] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 font-mono"
          />
        </div>
      )}

      {filters.preset === 'top_critical' && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Top</span>
          {TOP_N_OPTIONS.map(n => (
            <button
              key={n}
              onClick={() => onChange({ ...filters, topN: n })}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                filters.topN === n
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30 shadow-[0_0_10px_rgba(239,68,68,0.2)]'
                  : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      )}

      {filters.preset === 'risk_tier' && (
        <div className="flex items-center gap-2">
          {RISK_TIERS.map(tier => {
            const tierColors: Record<string, string> = {
              Critical: 'bg-red-500/20 text-red-400 border-red-500/30',
              High: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
              Medium: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
              Safe: 'bg-green-500/20 text-green-400 border-green-500/30',
            }
            return (
              <button
                key={tier}
                onClick={() => onChange({ ...filters, riskTier: filters.riskTier === tier ? undefined : tier })}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                  filters.riskTier === tier
                    ? tierColors[tier]
                    : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
                }`}
              >
                {tier}
              </button>
            )
          })}
        </div>
      )}

      {filters.preset === 'region' && (
        <div className="flex items-center gap-2 flex-wrap">
          {REGIONS.map(region => (
            <button
              key={region}
              onClick={() => onChange({ ...filters, region: filters.region === region ? undefined : region })}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                filters.region === region
                  ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                  : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
              }`}
            >
              {region}
            </button>
          ))}
        </div>
      )}

      {filters.preset === 'plan' && (
        <div className="flex items-center gap-2 flex-wrap">
          {PLANS.map(plan => (
            <button
              key={plan}
              onClick={() => onChange({ ...filters, plan: filters.plan === plan ? undefined : plan })}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                filters.plan === plan
                  ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                  : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
              }`}
            >
              {plan}
            </button>
          ))}
        </div>
      )}

      {filters.preset === 'month' && (
        <div className="flex items-center gap-1.5 flex-wrap">
          {MONTHS.map(month => (
            <button
              key={month}
              onClick={() => onChange({ ...filters, month: filters.month === month ? undefined : month })}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                filters.month === month
                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
              }`}
            >
              {month}
            </button>
          ))}
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Results count + clear */}
      <div className="flex items-center gap-3">
        <div className="text-xs text-slate-400 font-mono">
          <span className="text-white font-bold">{filteredCount.toLocaleString()}</span>
          <span className="mx-1">/</span>
          <span>{totalCustomers.toLocaleString()}</span>
          <span className="ml-1">shown</span>
        </div>
        {filters.preset !== 'all' && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
