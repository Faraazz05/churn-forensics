import React from 'react';
import { motion } from 'framer-motion';

const DRIFT_FEATURES = [
  { name: 'last_login_days_ago', psi: 0.34, status: 'critical' },
  { name: 'logins_per_week', psi: 0.28, status: 'critical' },
  { name: 'engagement_score', psi: 0.21, status: 'critical' },
  { name: 'support_tickets', psi: 0.18, status: 'monitor' },
  { name: 'nps_score', psi: 0.14, status: 'monitor' },
  { name: 'active_features', psi: 0.12, status: 'monitor' },
  { name: 'payment_failures', psi: 0.08, status: 'stable' },
  { name: 'session_duration', psi: 0.04, status: 'stable' },
];

export function DriftSignalPreview() {
  const getBarColor = (psi: number) => {
    if (psi > 0.20) return 'bg-[#EF4444]'; // Significant drift (red)
    if (psi >= 0.10) return 'bg-[#F59E0B]'; // Monitor (yellow)
    return 'bg-[#10B981]'; // Stable (green)
  };

  return (
    <section className="py-24 bg-[#0F1629] border-b border-[#1E2A45] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-4"
          >
            Catch Decline Before It Becomes Churn
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-lg text-[#64748B] max-w-2xl mx-auto"
          >
            Population Stability Index (PSI) tracks distributional shifts in user behavior,
            flagging subtle disengagement weeks before standard metrics crash.
          </motion.p>
        </div>

        <div className="max-w-4xl mx-auto mb-16">
          <div className="space-y-4 relative p-6 bg-[#0A0D1A] border border-[#1E2A45] rounded-xl shadow-2xl">
            {/* Reference Lines Container */}
            <div className="absolute top-0 bottom-0 left-[200px] right-6 pointer-events-none hidden sm:block">
              {/* 0.10 Line */}
              <div className="absolute left-[25%] top-0 bottom-0 border-l border-dashed border-[#F59E0B]/40 z-0">
                <span className="absolute top-2 -translate-x-1/2 bg-[#0A0D1A] text-[#F59E0B] text-[10px] px-1 font-mono">PSI 0.10</span>
              </div>
              {/* 0.20 Line */}
              <div className="absolute left-[50%] top-0 bottom-0 border-l border-dashed border-[#EF4444]/40 z-0">
                <span className="absolute top-2 -translate-x-1/2 bg-[#0A0D1A] text-[#EF4444] text-[10px] px-1 font-mono">PSI 0.20</span>
              </div>
            </div>

            <div className="pt-8 relative z-10">
              {DRIFT_FEATURES.map((feature, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row items-start sm:items-center mb-4 sm:mb-3">
                  <div className="w-[200px] shrink-0 font-mono text-sm text-[#F1F5F9] mb-2 sm:mb-0">
                    {feature.name}
                  </div>
                  <div className="flex-1 w-full bg-[#1E2A45] h-3 rounded-full overflow-hidden relative">
                    <motion.div
                      initial={{ scaleX: 0 }}
                      whileInView={{ scaleX: 1 }}
                      viewport={{ once: true, margin: "-50px" }}
                      transition={{ duration: 0.8, delay: idx * 0.1, ease: 'easeOut' }}
                      className={`h-full ${getBarColor(feature.psi)} rounded-full origin-left`}
                      style={{ width: `${(feature.psi / 0.40) * 100}%` }}
                    />
                  </div>
                  <div className="w-16 shrink-0 text-right sm:text-left sm:ml-4 font-mono text-sm font-bold text-[#F1F5F9]">
                    {feature.psi.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Early Warning Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-10">
          {[
            { name: 'last_login_days_ago', psi: 0.34, trend: 'increasing', level: 'HIGH', xai: true },
            { name: 'logins_per_week', psi: 0.28, trend: 'decreasing', level: 'HIGH', xai: true },
            { name: 'engagement_score', psi: 0.21, trend: 'decreasing', level: 'MED', xai: false },
          ].map((card, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: 0.2 + (idx * 0.1) }}
              className={`p-5 rounded-xl border bg-[#0A0D1A] ${
                card.level === 'HIGH' ? 'border-[#EF4444]/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : 'border-[#F59E0B]/50'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span className={`${card.level === 'HIGH' ? 'text-[#EF4444]' : 'text-[#F59E0B]'}`}>⚡</span>
                  <h4 className="font-mono text-xs text-[#F1F5F9] truncate" title={card.name}>{card.name}</h4>
                </div>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${card.level === 'HIGH' ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'bg-[#F59E0B]/20 text-[#F59E0B]'}`}>
                  {card.level}
                </span>
              </div>
              
              <div className="text-sm text-[#64748B] flex justify-between items-center bg-[#0F1629] p-2 rounded">
                <span>PSI = {card.psi}</span>
                <span className="flex items-center gap-1">
                  {card.trend === 'increasing' ? (
                    <svg className="w-3 h-3 text-[#EF4444]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
                  ) : (
                    <svg className="w-3 h-3 text-[#EF4444]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M23 18l-9.5-9.5-5 5L1 6"/><path d="M17 18h6v-6"/></svg>
                  )}
                  {card.trend}
                </span>
                {card.xai && (
                  <span className="text-[10px] text-[#10B981] font-bold ml-1" title="Confirmed by XAI">[XAI ✓]</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Retraining Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ delay: 0.5 }}
          className="max-w-4xl mx-auto mt-8 bg-[#EF4444]/10 border border-[#EF4444] rounded-lg p-4 flex items-center justify-center gap-3"
        >
          <svg className="w-6 h-6 text-[#EF4444]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span className="text-[#EF4444] font-medium text-sm md:text-base">
            Model Retraining Required — PSI &gt; 0.20 on 3+ features
          </span>
        </motion.div>

      </div>
    </section>
  );
}
