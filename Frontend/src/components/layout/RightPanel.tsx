import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../stores/appStore'

export function RightPanel() {
  const { isRightPanelOpen, closeRightPanel, rightPanelContent } = useAppStore()

  return (
    <AnimatePresence>
      {isRightPanelOpen && rightPanelContent && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#0A0D1A]/50 backdrop-blur-sm z-40 cursor-pointer"
            onClick={closeRightPanel}
          />
          <motion.div
            initial={{ x: 420 }}
            animate={{ x: 0 }}
            exit={{ x: 420 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 flex flex-col right-0 w-[420px] h-screen bg-[#0F1629] border-l border-[#1E2A45] z-50 shadow-2xl overflow-y-auto"
          >
            <div className="sticky top-0 bg-[#0F1629]/95 backdrop-blur p-4 border-b border-[#1E2A45] flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold text-slate-100 capitalize">
                {rightPanelContent.type.replace('-', ' ')}
              </h2>
              <button 
                onClick={closeRightPanel}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#1E2A45] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              <p className="text-sm text-slate-400">Context ID: {rightPanelContent.id}</p>
              <pre className="mt-4 p-4 text-xs font-mono bg-[#0A0D1A] text-blue-300 border border-[#1E2A45] rounded-lg overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(rightPanelContent.data, null, 2)}
              </pre>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
