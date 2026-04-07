import { ReactNode, useEffect, useState } from 'react';
import { X, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

interface ExpandedModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  details?: ReactNode;
  quickInsight?: ReactNode;
}

export function ExpandedModal({ isOpen, onClose, title, children, details, quickInsight }: ExpandedModalProps) {
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      setShowReport(false);
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => { document.body.style.overflow = 'auto'; }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/65 backdrop-blur-lg animate-in fade-in duration-300"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-[85vw] max-h-[92vh] flex flex-col shadow-2xl relative border border-white/15 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-5 border-b border-white/10 bg-white/[0.02] shrink-0">
          <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 drop-shadow-sm tracking-wide">{title}</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white transition-colors rounded-full hover:bg-white/10">
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto custom-scrollbar">
          <div className="p-8 flex flex-col lg:flex-row gap-8 min-h-0">
            {/* Left: Visualization */}
            <div className="flex-1 min-h-[420px] lg:min-h-[550px] relative pointer-events-auto">
              {children}
            </div>

            {/* Right: Unified insights panel */}
            {(quickInsight || details) && (
              <div className="lg:w-[420px] xl:w-[480px] flex flex-col gap-5 shrink-0">
                {/* Quick Insight Section (always visible) */}
                {quickInsight && (
                  <div className="glass-card p-6 bg-gradient-to-br from-purple-500/[0.08] to-blue-500/[0.05] border-purple-500/20">
                    <h3 className="text-base font-bold text-purple-400 mb-4 flex items-center gap-2 border-b border-purple-500/20 pb-3">
                      <Sparkles className="text-purple-400" size={18} /> Quick Insight
                    </h3>
                    <div className="text-slate-300 space-y-3 leading-relaxed text-[15px]">
                      {quickInsight}
                    </div>
                  </div>
                )}

                {/* Expandable Detailed Report */}
                {details && (
                  <div className="glass-card bg-gradient-to-br from-blue-500/[0.06] to-purple-500/[0.04] border-blue-500/20 overflow-hidden">
                    <button
                      onClick={() => setShowReport(!showReport)}
                      className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-white/[0.03] transition-colors"
                    >
                      <h3 className="text-base font-bold text-blue-400 flex items-center gap-2">
                        <Sparkles className="text-blue-400" size={18} /> AI Diagnostic Report
                      </h3>
                      {showReport ? <ChevronUp className="text-blue-400" size={18} /> : <ChevronDown className="text-blue-400" size={18} />}
                    </button>
                    <div
                      className={`transition-all duration-500 ease-in-out overflow-hidden ${showReport ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'}`}
                    >
                      <div className="px-6 pb-6 text-slate-300 space-y-4 leading-relaxed text-[15px] prose prose-invert">
                        {details}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
