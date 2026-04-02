import React from 'react';
import { motion } from 'framer-motion';

const fadeUpVariant = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

interface HeroSectionProps {
  onDemoClick: () => void;
  onAnalysisClick: () => void;
}

export function HeroSection({ onDemoClick, onAnalysisClick }: HeroSectionProps) {
  return (
    <section className="relative w-full min-h-screen flex flex-col justify-center items-center px-4 pt-24 pb-16 z-10 pointer-events-none">
      <div className="max-w-5xl mx-auto text-center pointer-events-auto">
        
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center"
        >
          {/* Animated Badge */}
          <motion.div
            variants={fadeUpVariant}
            className="flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full bg-[#0F1629] border border-[#1E2A45] shadow-lg"
          >
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#3B82F6] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#3B82F6]"></span>
            </span>
            <span className="text-xs font-medium text-[#64748B] tracking-wide uppercase">
              500K+ Customers &middot; 12-Month Dataset &middot; 8-Phase Pipeline
            </span>
          </motion.div>

          {/* Heading */}
          <motion.h1
            variants={fadeUpVariant}
            className="text-5xl md:text-6xl lg:text-[64px] font-bold text-[#F1F5F9] leading-[1.1] tracking-[-0.02em] mb-6"
          >
            Turn Customer Data Into <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]">
              Retention Intelligence
            </span>
          </motion.h1>

          {/* Subtext */}
          <motion.p
            variants={fadeUpVariant}
            className="max-w-3xl text-lg text-[#64748B] leading-[1.7] mb-10"
          >
            The only churn platform that combines ML prediction, consensus XAI, segmentation,
            drift detection, and LLM insights into one diagnostic system.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={fadeUpVariant}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12 w-full sm:w-auto"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              onClick={onDemoClick}
              className="w-full sm:w-auto px-8 py-3.5 bg-[#3B82F6] text-[#F1F5F9] font-medium rounded-lg shadow-[0_0_40px_rgba(59,130,246,0.3)] hover:shadow-[0_0_60px_rgba(59,130,246,0.5)] transition-shadow flex items-center justify-center gap-2"
            >
              View Demo
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onAnalysisClick}
              className="w-full sm:w-auto px-8 py-3.5 text-[#8B5CF6] font-medium bg-transparent border border-[#8B5CF6]/50 rounded-lg hover:bg-[#8B5CF6]/10 transition-colors"
            >
              Start Real Analysis
            </motion.button>
          </motion.div>

          {/* Trust Indicators */}
          <motion.div
            variants={fadeUpVariant}
            className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-sm font-medium text-[#64748B]"
          >
            <div className="flex items-center gap-2">
              <svg className="text-[#10B981] w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              AUC 0.9273
            </div>
            <div className="flex items-center gap-2">
              <svg className="text-[#10B981] w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              SHAP + LIME + AIX360
            </div>
            <div className="flex items-center gap-2">
              <svg className="text-[#10B981] w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              500k rows processed
            </div>
          </motion.div>
        </motion.div>
        
      </div>
    </section>
  );
}
