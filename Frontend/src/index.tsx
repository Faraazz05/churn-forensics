import { motion } from 'framer-motion'
import { ArrowRight, Hexagon, Brain, Database, ShieldAlert, Activity } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#0A0D1A] text-slate-50 font-sans selection:bg-blue-500/30 overflow-hidden relative">
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] pointer-events-none translate-y-1/2 -translate-x-1/2" />

      <header className="fixed top-0 inset-x-0 h-[72px] bg-[#0A0D1A]/80 backdrop-blur-md border-b border-[#1E2A45] z-50 flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <Hexagon className="w-8 h-8 text-blue-500 fill-blue-500/20" />
          <span className="font-bold text-xl tracking-wide text-white">Forensics<span className="text-blue-500">.ai</span></span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#features" className="hover:text-white transition">Platform</a>
          <a href="#xai" className="hover:text-white transition">Explainability</a>
          <a href="#demo" className="hover:text-white transition">Live Demo</a>
        </nav>
        <button className="px-5 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm font-bold text-white hover:bg-white/10 transition" onClick={() => navigate('/demo')}>
          Enter Application
        </button>
      </header>

      <main className="pt-[160px] pb-24 px-8 max-w-7xl mx-auto relative z-10 flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-bold uppercase tracking-widest mb-8"
        >
          <span className="relative flex h-2 w-2">
             <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
             <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          Next-Gen AI Intelligence
        </motion.div>
        
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-6xl md:text-8xl font-black text-white tracking-tight mb-8 leading-[1.1]"
        >
          Customer Health<br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
            Forensics
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed"
        >
          Predictive pipeline built on state-of-the-art XAI algorithms. Catch algorithmic drift, surface critical churn segments, and interpret SHAP force bounds in real-time.
        </motion.p>

        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.6, delay: 0.3 }}
           className="flex flex-col sm:flex-row items-center gap-6"
        >
           <button onClick={() => navigate('/upload')} className="px-8 py-4 bg-blue-600 text-white font-bold rounded-xl shadow-[0_0_40px_rgba(37,99,235,0.4)] hover:shadow-[0_0_60px_rgba(37,99,235,0.6)] hover:-translate-y-1 transition-all flex items-center gap-3">
             <Database className="w-5 h-5" /> Connect Dataset
           </button>
           <button onClick={() => navigate('/demo')} className="px-8 py-4 bg-transparent border border-white/20 text-white font-bold rounded-xl hover:bg-white/5 transition-all flex items-center gap-3 group">
             Run Live Demo <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
           </button>
        </motion.div>

        <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8 w-full text-left">
           {[
             { title: 'Global Explainability', desc: 'Precise SHAP tracking across 500k features. No black boxes.', icon: Brain, c: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
             { title: 'Algorithmic Drift Watch', desc: 'Real-time PSI divergence reports flag model decay over time.', icon: ShieldAlert, c: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
             { title: 'Revenue Correlation', desc: 'Direct mapping of predictive intelligence to MRI risk impacts.', icon: Activity, c: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
           ].map((ft, i) => (
             <motion.div
               key={i}
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ duration: 0.6, delay: 0.4 + (i * 0.1) }}
               className="bg-[#0F1629] p-8 rounded-2xl border border-[#1E2A45] shadow-xl relative overflow-hidden group hover:border-[#3B82F6]/50 transition-colors"
             >
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center border mb-6 transition-transform group-hover:scale-110 ${ft.c}`}>
                   <ft.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{ft.title}</h3>
                <p className="text-slate-400 leading-relaxed">{ft.desc}</p>
             </motion.div>
           ))}
        </div>
      </main>
    </div>
  )
}
