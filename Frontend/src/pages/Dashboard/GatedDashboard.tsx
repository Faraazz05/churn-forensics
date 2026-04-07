/**
 * GatedDashboard.tsx
 * ==================
 * Renders the Dashboard blurred in the background with the ProductGate
 * overlay on top. This is used for /analysis/dashboard.
 *
 * The gate is NEVER dismissable — no state, no toggle, no escape.
 */
import { Dashboard } from '../Dashboard'
import { ProductGate } from '../../components/ui/ProductGate'

export function GatedDashboard() {
  return (
    <div className="relative">
      {/* Dashboard rendered behind — blurred and non-interactive */}
      <div
        className="pointer-events-none select-none"
        style={{ filter: 'blur(6px)', opacity: 0.35 }}
        aria-hidden="true"
      >
        <Dashboard />
      </div>

      {/* Gate — always rendered, always on top, no way to close */}
      <ProductGate />
    </div>
  )
}
