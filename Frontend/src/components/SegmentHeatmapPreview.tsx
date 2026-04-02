import React, { useState } from 'react';
import { motion } from 'framer-motion';

const ROWS = ['Basic', 'Pro', 'Enterprise'];
const COLS = ['North', 'South', 'East', 'West', 'Central'];

// Hardcoded churn values
// >30% red, 20-30% orange, 10-20% yellow, <10% green
const HEATMAP_DATA = [
  // Basic
  [0.18, 0.21, 0.15, 0.32, 0.11],
  // Pro
  [0.05, 0.08, 0.41, 0.14, 0.09],
  // Enterprise
  [0.02, 0.04, 0.06, 0.03, 0.01],
];

const getCellColor = (val: number) => {
  if (val > 0.3) return 'bg-[#EF4444] text-white'; // Red
  if (val >= 0.2 && val <= 0.3) return 'bg-[#F97316] text-white'; // Orange
  if (val >= 0.1 && val < 0.2) return 'bg-[#EAB308] text-[#0A0D1A]'; // Yellow
  return 'bg-[#10B981] text-white'; // Green
};

const getOpacity = (val: number) => {
  // subtle opacity scaling based on value
  if (val > 0.3) return 0.9;
  if (val >= 0.2) return 0.8;
  if (val >= 0.1) return 0.7;
  return 0.5 + (val * 2);
};

export function SegmentHeatmapPreview() {
  const [hoveredCell, setHoveredCell] = useState<{r: number, c: number, v: number} | null>(null);

  return (
    <section className="py-24 bg-[#0A0D1A] border-b border-[#1E2A45]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-4">
            Segment Intelligence
          </h2>
          <p className="text-lg text-[#64748B] max-w-2xl mx-auto">
            Find exactly who is degrading. Cross-sectional cohort tracking surfaces
            micro-segments accelerating toward churn before they impact top-line metrics.
          </p>
        </motion.div>

        {/* Heatmap Grid */}
        <div className="max-w-4xl mx-auto mb-16 relative">
          <div className="overflow-x-auto pb-6">
            <div className="min-w-[600px]">
              {/* Header Row */}
              <div className="flex mb-2">
                <div className="w-24 shrink-0"></div>
                {COLS.map(col => (
                  <div key={col} className="flex-1 text-center text-xs font-semibold text-[#64748B] uppercase tracking-wider">
                    {col}
                  </div>
                ))}
              </div>

              {/* Data Rows */}
              {ROWS.map((rowName, rIndex) => (
                <div key={rowName} className="flex mb-2 items-center">
                  <div className="w-24 shrink-0 text-sm font-medium text-[#F1F5F9] text-right pr-4">
                    {rowName}
                  </div>
                  {COLS.map((colName, cIndex) => {
                    const val = HEATMAP_DATA[rIndex][cIndex];
                    const isHovered = hoveredCell?.r === rIndex && hoveredCell?.c === cIndex;
                    
                    return (
                      <div 
                        key={`${rIndex}-${cIndex}`} 
                        className="flex-1 px-1 relative cursor-pointer"
                        onMouseEnter={() => setHoveredCell({r: rIndex, c: cIndex, v: val})}
                        onMouseLeave={() => setHoveredCell(null)}
                      >
                        <div 
                          className={`h-12 w-full rounded shadow-sm flex items-center justify-center text-xs font-bold transition-transform ${getCellColor(val)} ${isHovered ? 'scale-110 z-10 shadow-lg ring-2 ring-white/50' : ''}`}
                          style={{ opacity: isHovered ? 1 : getOpacity(val) }}
                        >
                          {(val * 100).toFixed(0)}%
                        </div>
                        
                        {/* Tooltip */}
                        {isHovered && (
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-xs z-20 pointer-events-none">
                            <div className="bg-[#0A0D1A] border border-[#1E2A45] rounded-lg shadow-xl p-3 text-xs text-[#F1F5F9] whitespace-nowrap">
                              <span className="font-bold text-[#3B82F6]">{rowName} / {colName}: {(val * 100).toFixed(0)}% churn</span>
                              <div className="text-[#64748B] mt-1 space-x-2">
                                <span>+0.19Δ</span>
                                <span>&middot;</span>
                                <span>$125,000 at risk</span>
                              </div>
                            </div>
                            <div className="w-2 h-2 bg-[#0A0D1A] border-r border-b border-[#1E2A45] rotate-45 mx-auto -mt-[5px]" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Degrading Segment Alert Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {[
            { tag: 'plan_type=pro', churn: '0.41', delta: '+0.19', risk: '$125k', status: 'ACCELERATING' },
            { tag: 'region=East', churn: '0.38', delta: '+0.14', risk: '$98k', status: 'DEGRADING' },
            { tag: 'contract=monthly', churn: '0.35', delta: '+0.11', risk: '$87k', status: 'DEGRADING' },
          ].map((alert, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: idx * 0.15 }}
              className="bg-[#0F1629] rounded-xl overflow-hidden border border-[#1E2A45] flex shadow-lg shrink-0"
            >
              <div className="w-1.5 bg-[#EF4444] shrink-0" />
              <div className="p-5 flex-1">
                <div className="flex justify-between items-start mb-3">
                  <span className="font-mono text-sm text-[#F1F5F9] bg-[#1E2A45] px-2 py-0.5 rounded">
                    {alert.tag}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    alert.status === 'ACCELERATING' ? 'bg-[#EF4444]/20 text-[#EF4444] animate-pulse' : 'bg-[#F97316]/20 text-[#F97316]'
                  }`}>
                    {alert.status}
                  </span>
                </div>
                
                <div className="flex gap-4">
                  <div className="flex flex-col">
                    <span className="text-xs text-[#64748B] uppercase">Churn</span>
                    <span className="text-lg font-bold text-[#F1F5F9]">{alert.churn}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs text-[#64748B] uppercase">Delta</span>
                    <span className="text-lg font-bold text-[#EF4444]">{alert.delta}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs text-[#64748B] uppercase">At Risk</span>
                    <span className="text-lg font-bold text-[#F1F5F9]">{alert.risk}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
