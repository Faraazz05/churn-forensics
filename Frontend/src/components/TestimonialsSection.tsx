import React from 'react';
import { motion } from 'framer-motion';

const QUOTES = [
  {
    text: "The XAI consensus system completely changed how our retention team operates. We no longer guess why an account is marked high-risk; we know exactly which features are driving the score.",
    author: "Director of Customer Success",
    company: "Enterprise SaaS Platform"
  },
  {
    text: "We caught significant degradation in our Pro tier user base 5 weeks before it would have shown up in our quarterly churn metrics, thanks to the cohort tracking.",
    author: "VP of Data Science",
    company: "Global Fintech"
  },
  {
    text: "The LLM Insight Engine translating complex SHAP values into simple English emails for my account managers is arguably the highest ROI feature we've ever deployed.",
    author: "Chief Revenue Officer",
    company: "B2B Cloud Services"
  }
];

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

const fadeUpVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
};

export function TestimonialsSection() {
  return (
    <section className="py-24 bg-[#0F1629] border-b border-[#1E2A45] relative overflow-hidden">
      
      {/* Decorative Grid SVG */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#F1F5F9" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#gridPattern)" />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUpVariant}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-4">
            Proven in Production
          </h2>
          <p className="text-lg text-[#64748B] max-w-2xl mx-auto">
            Deployed across hundreds of thousands of live user profiles, helping data teams
            and revops speak the same language.
          </p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={staggerContainer}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {QUOTES.map((quote, idx) => (
            <motion.div
              key={idx}
              variants={fadeUpVariant}
              whileHover={{ y: -5 }}
              className="bg-[#0A0D1A] rounded-2xl p-8 border border-[#1E2A45] shadow-[0_4px_20px_rgba(0,0,0,0.2)] flex flex-col justify-between hover:border-[#3B82F6]/50 transition-colors"
            >
              <svg className="w-10 h-10 text-[#3B82F6]/20 mb-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
              </svg>
              
              <p className="text-[#F1F5F9] leading-relaxed mb-8 flex-1">
                "{quote.text}"
              </p>
              
              <div>
                <p className="text-[#64748B] font-bold text-sm">
                  {quote.author}
                </p>
                <p className="text-[#3B82F6] text-sm">
                  {quote.company}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
