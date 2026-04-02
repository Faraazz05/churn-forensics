import { useState } from 'react'

export function Tooltip({ content, children }: { content: string, children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(false)

  return (
    <div 
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-navy-700 border border-navy-600 outline outline-1 outline-black/30 rounded text-xs text-slate-200 whitespace-nowrap z-50">
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-navy-700"></div>
        </div>
      )}
    </div>
  )
}
