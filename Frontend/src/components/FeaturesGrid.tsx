import React from 'react';
import { motion } from 'framer-motion';

const fadeUpVariant = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
};

const FEATURES = [
  {
    title: 'Per-Customer Prediction',
    desc: 'Probability and discrete risk tier assignments (Critical, High, Medium, Safe) based on dynamic thresholding.',
    tech: 'XGBoost · CatBoost',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    )
  },
  {
    title: 'XAI Consensus',
    desc: 'Agreement-based pipeline. Issues HIGH confidence only when SHAP, LIME, and AIX360 independently align.',
    tech: 'SHAP · LIME · AIX360',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
    )
  },
  {
    title: 'Segmentation Tracking',
    desc: 'Temporal degradation tracing. Quickly identifies accelerating_risk subgroups well before widespread spikes occur.',
    tech: 'K-Means · DBSCAN',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
        <line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
    )
  },
  {
    title: 'Drift Early Warning',
    desc: 'Proactive detection using PSI and KS-test to flag leading drift indicators 4-6 weeks before a retention crisis.',
    tech: 'Evidently AI · Scipy',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 3v18h18"/>
        <path d="m19 9-5 5-4-4-3 3"/>
      </svg>
    )
  },
  {
    title: 'LLM Insight Engine',
    desc: 'Translates statistical anomalies into plain English: WHAT changed + WHY it happened + WHAT you should do next.',
    tech: 'LangChain · GPT-4',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    )
  },
  {
    title: 'RL Recommender',
    desc: 'Q-learning optimization agent continuously learns and suggests which intervention actions perform best over time.',
    tech: 'Q-Learning · Actions',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    )
  }
];

export function FeaturesGrid() {
  return (
    <section className="py-24 bg-[#0A0D1A] border-b border-[#1E2A45]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
            className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-4"
          >
            What This System Actually Does
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-lg text-[#64748B] max-w-2xl mx-auto"
          >
            A multi-layered architecture working in concert to identify, explain, and mitigate customer churn.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, idx) => (
            <motion.div
              key={idx}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-50px" }}
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0, transition: { duration: 0.5, delay: idx * 0.1 } }
              }}
              whileHover={{ scale: 1.02 }}
              className="group relative rounded-xl bg-[#0F1629] p-[1px] overflow-hidden"
            >
              {/* Animated gradient border on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl" />
              
              <div className="relative h-full flex flex-col p-8 bg-[#0F1629] rounded-[11px] border border-[#1E2A45] group-hover:border-transparent transition-colors z-10">
                <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-[#3B82F6]/10 text-[#3B82F6] mb-6">
                  {feature.icon}
                </div>
                
                <h3 className="text-xl font-bold text-[#F1F5F9] mb-3">
                  {feature.title}
                </h3>
                
                <p className="text-[#64748B] leading-relaxed mb-8 flex-grow">
                  {feature.desc}
                </p>
                
                <div className="mt-auto">
                  <span className="inline-block px-3 py-1.5 bg-[#1E2A45]/50 text-xs font-medium text-[#8B5CF6] rounded-md font-mono">
                    {feature.tech}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
