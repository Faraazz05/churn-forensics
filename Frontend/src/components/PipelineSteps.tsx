import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const fadeUpVariant = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
};

const PHASES = [
  { id: 1, title: 'Data Ingestion', desc: '500k records, 12-month snapshots, CSV/SQL' },
  { id: 2, title: 'Feature Engineering', desc: '12 domain features, modular registry' },
  { id: 3, title: 'ML Model Selection', desc: 'Size-aware: XGBoost vs Logistic, AUC primary' },
  { id: 4, title: 'Consensus XAI', desc: 'SHAP primary + LIME + AIX360 agreement-based' },
  { id: 5, title: 'Segmentation', desc: 'Plan × Region × Behavior degradation tracking' },
  { id: 6, title: 'Drift Detection', desc: 'PSI + KS-test + early warning signals' },
  { id: 7, title: 'Insight Engine', desc: 'ANN + RL + LLM narrative generation' },
  { id: 8, title: 'FastAPI Backend', desc: '10 endpoints, async, role-based auth' },
];

export function PipelineSteps() {
  const [activePhase, setActivePhase] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setActivePhase((prev) => (prev % 8) + 1);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="py-24 bg-[#0A0D1A] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          variants={fadeUpVariant}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-4">
            8-Phase Intelligence Pipeline
          </h2>
          <p className="text-lg text-[#64748B] max-w-2xl mx-auto">
            From raw historical data to actionable retention strategies in a unified modular system.
          </p>
        </motion.div>

        {/* Mobile: Horizontal scroll, Desktop: Grid */}
        <div className="flex overflow-x-auto pb-8 md:grid md:grid-cols-4 md:grid-rows-2 gap-6 snap-x snap-mandatory hide-scroll">
          {PHASES.map((phase) => {
            const isActive = activePhase === phase.id;
            return (
              <motion.div
                key={phase.id}
                whileHover={{ y: -4, scale: 1.02 }}
                className={`snap-center shrink-0 w-[280px] md:w-auto relative flex flex-col p-6 rounded-xl bg-[#0F1629] border transition-all duration-300 ${
                  isActive
                    ? 'border-[#3B82F6] shadow-[0_0_20px_rgba(59,130,246,0.15)]'
                    : 'border-[#1E2A45]'
                } hover:border-[#3B82F6] hover:shadow-[0_0_20px_rgba(59,130,246,0.1)] cursor-pointer`}
                onMouseEnter={() => setActivePhase(phase.id)}
              >
                <div className="flex items-center gap-4 mb-4">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-lg text-sm font-bold shadow-inner ${
                      isActive
                        ? 'bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] text-white'
                        : 'bg-[#1E2A45] text-[#F1F5F9]'
                    }`}
                  >
                    {phase.id}
                  </div>
                  <h3 className="text-lg font-semibold text-[#F1F5F9] leading-tight flex-1">
                    {phase.title}
                  </h3>
                </div>

                <p className="text-sm text-[#64748B] leading-[1.6]">
                  {phase.desc}
                </p>

                {/* Animated active indicator pip */}
                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      layoutId="activePipelineIndicator"
                      className="absolute bottom-0 left-0 h-1 w-full bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] rounded-b-xl"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    />
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
        
        {/* Custom CSS for hiding the horizontal scrollbar but allowing scroll */}
        <style dangerouslySetInnerHTML={{ __html: `
          .hide-scroll::-webkit-scrollbar { display: none; }
          .hide-scroll { -ms-overflow-style: none; scrollbar-width: none; }
        `}} />
      </div>
    </section>
  );
}
