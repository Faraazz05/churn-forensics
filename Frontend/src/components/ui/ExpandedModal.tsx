import { ReactNode, useEffect } from 'react';
import { X, Sparkles } from 'lucide-react';

interface ExpandedModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  details?: ReactNode;
}

export function ExpandedModal({ isOpen, onClose, title, children, details }: ExpandedModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => { document.body.style.overflow = 'auto'; }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
      <div className="glass-panel w-full max-w-7xl max-h-[95vh] flex flex-col shadow-2xl relative border border-white/20">
        <div className="flex items-center justify-between px-8 py-5 border-b border-white/10 bg-white/[0.02]">
          <h2 className="text-2xl font-bold text-white tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 drop-shadow-sm">{title}</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white transition-colors rounded-full hover:bg-white/10">
            <X size={24} />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-8 flex flex-col lg:flex-row gap-8 custom-scrollbar relative">
          <div className="flex-1 min-h-[400px] lg:min-h-[600px] relative pointer-events-auto">
            {children}
          </div>
          {details && (
            <div className="lg:w-[400px] glass-card p-6 h-fit bg-gradient-to-br from-blue-500/[0.05] to-purple-500/[0.05] border-blue-500/20">
              <h3 className="text-lg font-bold text-blue-400 mb-5 flex items-center gap-2 border-b border-blue-500/20 pb-3">
                <Sparkles className="text-blue-400" size={20} /> AI Diagnostic Report
              </h3>
              <div className="text-slate-300 space-y-4 leading-relaxed text-[15px] prose prose-invert">
                {details}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
