import React, { useState, useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';

const fadeUpVariant = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
};

interface CounterProps {
  value: number;
  label: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

function AnimatedCounter({ value, label, prefix = '', suffix = '', decimals = 0 }: CounterProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const [currentValue, setCurrentValue] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    
    let startTimestamp: number | null = null;
    const duration = 1500; // 1.5s
    
    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      
      // easeOutExpo
      const expo = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCurrentValue(expo * value);
      
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };
    
    window.requestAnimationFrame(step);
  }, [isInView, value]);

  const formattedValue = decimals > 0 
    ? currentValue.toFixed(decimals)
    : Math.floor(currentValue).toLocaleString();

  return (
    <div ref={ref} className="flex flex-col items-center justify-center p-4">
      <div className="text-3xl md:text-4xl font-bold text-[#F1F5F9] font-['JetBrains_Mono',monospace] mb-2 tracking-tight">
        {prefix}{formattedValue}{suffix}
      </div>
      <div className="text-xs md:text-sm font-medium text-[#64748B] uppercase tracking-wider text-center">
        {label}
      </div>
    </div>
  );
}

export function MetricsBar() {
  return (
    <section className="bg-[#0A0D1A] border-y border-[#1E2A45] py-12 relative z-20">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeUpVariant}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="grid grid-cols-2 md:grid-cols-5 divide-x divide-y md:divide-y-0 divide-[#1E2A45] border border-[#1E2A45] rounded-xl bg-[#0F1629]/50 overflow-hidden">
          
          <AnimatedCounter 
            value={500} 
            label="Customers Analyzed" 
            suffix=",000+" 
          />
          <AnimatedCounter 
            value={0.9273} 
            label="Val AUC Score" 
            decimals={4} 
          />
          <AnimatedCounter 
            value={22} 
            label="Avg Churn Rate" 
            suffix="%" 
          />
          <AnimatedCounter 
            value={12} 
            label="Months Drift Tracking" 
          />
          <AnimatedCounter 
            value={3} 
            label="XAI Methods" 
          />
          
        </div>
      </motion.div>
    </section>
  );
}
