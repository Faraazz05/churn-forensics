import React from 'react';
import { motion } from 'framer-motion';

const XAI_FEATURES = [
  { name: 'last_login_days_ago', score: 0.91, conf: 'HIGH', impact: 'risk+', width: '92%' },
  { name: 'logins_per_week', score: 0.74, conf: 'HIGH', impact: 'risk-', width: '74%' },
  { name: 'payment_failures', score: 0.68, conf: 'MEDIUM', impact: 'risk+', width: '68%' },
  { name: 'nps_score', score: 0.61, conf: 'HIGH', impact: 'risk-', width: '61%' },
  { name: 'support_tickets', score: 0.52, conf: 'LOW', impact: 'risk+', width: '52%' },
];

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.2 } }
};

const barVariant = {
  hidden: { scaleX: 0, opacity: 0 },
  visible: { scaleX: 1, opacity: 1, transition: { duration: 0.8, ease: "easeOut" } }
};

export function XAIShowcase() {
  return (
    <section className="py-24 bg-[#0A0D1A] border-b border-[#1E2A45] overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-16 items-center">
          
          {/* Left Text Explanation */}
          <div className="lg:w-1/2">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              className="text-3xl md:text-[40px] font-semibold text-[#F1F5F9] mb-6 leading-tight"
            >
              Consensus Explainability <br />
              <span className="text-[#8B5CF6]">Not Just Feature Importance</span>
            </motion.h2>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ delay: 0.1 }}
              className="text-lg text-[#64748B] mb-8 leading-[1.7]"
            >
              Instead of relying on a single explainability method which can be mathematically deceptive, 
              we compute global and local attributions across three distinct algorithms.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ delay: 0.2 }}
              className="space-y-4 mb-8"
            >
              <div className="flex items-center gap-4 bg-[#0F1629] p-4 rounded-xl border border-[#1E2A45]">
                <div className="w-12 h-12 bg-[#3B82F6]/10 text-[#3B82F6] flex items-center justify-center rounded-lg font-bold">1</div>
                <div>
                  <h4 className="text-[#F1F5F9] font-medium">SHAP (Primary · 40%)</h4>
                  <p className="text-sm text-[#64748B]">Shapley values for additive feature attribution</p>
                </div>
              </div>

              <div className="flex items-center gap-4 bg-[#0F1629] p-4 rounded-xl border border-[#1E2A45]">
                <div className="w-12 h-12 bg-[#8B5CF6]/10 text-[#8B5CF6] flex items-center justify-center rounded-lg font-bold">2</div>
                <div>
                  <h4 className="text-[#F1F5F9] font-medium">LIME (Validator · 30%)</h4>
                  <p className="text-sm text-[#64748B]">Local interpretable model-agnostic surrogate</p>
                </div>
              </div>

              <div className="flex items-center gap-4 bg-[#0F1629] p-4 rounded-xl border border-[#1E2A45]">
                <div className="w-12 h-12 bg-[#10B981]/10 text-[#10B981] flex items-center justify-center rounded-lg font-bold">3</div>
                <div>
                  <h4 className="text-[#F1F5F9] font-medium">AIX360 (Validator · 30%)</h4>
                  <p className="text-sm text-[#64748B]">Independent rule-based anchoring</p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ delay: 0.3 }}
              className="bg-[#10B981]/10 border border-[#10B981]/20 p-4 rounded-lg flex items-center gap-3"
            >
              <svg className="w-5 h-5 text-[#10B981] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-[#F1F5F9] font-medium">
                HIGH confidence = all 3 methods agree on direction + rank
              </p>
            </motion.div>
          </div>

          {/* Right Visual Breakdown */}
          <div className="lg:w-1/2 w-full">
            <div className="bg-[#0F1629] border border-[#1E2A45] rounded-xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#1E2A45]">
                <div>
                  <h3 className="text-[#F1F5F9] font-semibold">Consensus Output: Customer #892</h3>
                  <p className="text-xs text-[#64748B] mt-1 font-mono">Prediction: 84.2% Churn Probability</p>
                </div>
                <div className="px-3 py-1 bg-[#EF4444]/20 text-[#EF4444] text-xs font-bold rounded">
                  CRITICAL RISK
                </div>
              </div>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
                className="space-y-5"
              >
                {XAI_FEATURES.map((feature, idx) => {
                  const isHigh = feature.conf === 'HIGH';
                  const isMedium = feature.conf === 'MEDIUM';
                  const confColor = isHigh ? 'border-[#10B981]' : isMedium ? 'border-[#F59E0B]' : 'border-[#EF4444]';
                  const confTextColor = isHigh ? 'text-[#10B981]' : isMedium ? 'text-[#F59E0B]' : 'text-[#EF4444]';
                  
                  const riskColor = feature.impact === 'risk+' ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'bg-[#10B981]/20 text-[#10B981]';
                  const barColor = feature.impact === 'risk+' ? 'bg-[#EF4444]' : 'bg-[#10B981]';

                  return (
                    <div key={idx} className="relative group">
                      <div className="flex justify-between items-end mb-2 text-sm font-mono">
                        <span className="text-[#F1F5F9]">{feature.name}</span>
                        <div className="flex items-center gap-3">
                          <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${confColor} ${confTextColor}`}>
                            {feature.conf} conf
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${riskColor}`}>
                            {feature.impact}
                          </span>
                        </div>
                      </div>

                      <div className="h-2 w-full bg-[#1E2A45] rounded-full overflow-hidden">
                        <motion.div
                          variants={barVariant}
                          className={`h-full ${barColor} rounded-full origin-left opacity-80`}
                          style={{ width: feature.width }}
                        />
                      </div>
                      
                      <div className="mt-1 flex justify-between text-xs text-[#64748B] font-mono">
                        <span>0.00</span>
                        <span>abs(score): {feature.score}</span>
                      </div>
                    </div>
                  );
                })}
              </motion.div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
