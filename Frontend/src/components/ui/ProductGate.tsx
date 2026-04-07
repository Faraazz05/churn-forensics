/**
 * ProductGate.tsx
 * ================
 * Full-screen, un-dismissable overlay shown over /analysis/dashboard.
 * No close button — users MUST contact the creator to access live mode.
 *
 * TO UPDATE EMAIL: change CREATOR_EMAIL below.
 */

const CREATOR_EMAIL = 'sp_mohdfaraz@outlook.com'

export function ProductGate() {
  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      style={{ backdropFilter: 'blur(16px)', background: 'rgba(5, 8, 22, 0.85)' }}
    >
      {/* Ambient glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-blue-600/10 blur-[120px]" />
        <div className="absolute bottom-1/4 left-1/2 -translate-x-1/2 w-[400px] h-[400px] rounded-full bg-purple-600/10 blur-[100px]" />
      </div>

      <div className="relative max-w-lg w-full mx-6">
        {/* Card */}
        <div
          className="rounded-2xl border border-white/10 overflow-hidden shadow-[0_0_80px_rgba(59,130,246,0.15)]"
          style={{ background: 'linear-gradient(135deg, rgba(15,22,45,0.98) 0%, rgba(10,13,26,0.98) 100%)' }}
        >
          {/* Top accent bar */}
          <div className="h-1 w-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500" />

          <div className="p-10 flex flex-col items-center text-center gap-6">
            {/* Lock icon */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600/30 to-purple-600/30 border border-blue-500/30 flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.3)]">
              <svg className="w-10 h-10 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>

            {/* Heading */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-widest mb-4">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                Premium Access Required
              </div>
              <h2 className="text-2xl font-bold text-white mb-3 leading-tight">
                Live Dashboard is<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  Restricted
                </span>
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed">
                The live analysis dashboard is part of the full licensed product.
                You're currently viewing the public demo — explore the demo dashboard to see a preview of the full system.
              </p>
            </div>

            {/* Divider */}
            <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

            {/* Contact CTA */}
            <div className="flex flex-col items-center gap-3 w-full">
              <p className="text-slate-500 text-xs uppercase tracking-wider font-semibold">Want the full product?</p>
              <a
                href={`mailto:${CREATOR_EMAIL}?subject=Customer%20Health%20Forensics%20%E2%80%94%20Full%20Product%20Enquiry`}
                className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-semibold text-white transition-all duration-300
                  bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500
                  shadow-[0_0_25px_rgba(59,130,246,0.4)] hover:shadow-[0_0_40px_rgba(59,130,246,0.6)]
                  border border-blue-400/30 hover:border-blue-300/50 active:scale-95"
              >
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Contact Creator
              </a>
              <p className="text-slate-600 text-xs">{CREATOR_EMAIL}</p>
            </div>

            {/* Redirect to demo */}
            <div className="w-full pt-1">
              <a
                href="/demo/dashboard"
                className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-slate-400
                  hover:text-slate-200 transition-all duration-200 border border-white/5 hover:border-white/10
                  hover:bg-white/5 text-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                View Demo Dashboard Instead
              </a>
            </div>
          </div>
        </div>

        {/* Footer note */}
        <p className="text-center text-slate-700 text-xs mt-6">
          Customer Health Forensics — Full Product is licensed & protected.
        </p>
      </div>
    </div>
  )
}
