export default function TopBar({ briefing = 'All systems nominal.', connected = true }) {
  return (
    <header className="fixed top-0 left-16 right-0 z-50 flex items-center justify-center px-6 pointer-events-none">
      <div className="dynamic-island mt-4 mx-auto max-w-xl w-full pointer-events-auto">
        {/* Left: blur_on icon + label */}
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-primary text-sm">blur_on</span>
          <span className="font-medium uppercase tracking-[0.2em] text-[10px] text-[#c6c6c8]">
            Dynamic Briefing
          </span>
        </div>

        {/* Center: scrolling briefing text */}
        <div className="flex-1 overflow-hidden relative px-4">
          <p className="marquee-text text-[10px] tracking-wide text-primary-fixed whitespace-nowrap">
            {briefing}
          </p>
        </div>

        {/* Right: connection indicator */}
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-tertiary shadow-[0_0_8px_#ffdd79]' : 'bg-error'}`} />
          <span className={`text-[10px] font-mono ${connected ? 'text-tertiary' : 'text-error'}`}>
            {connected ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  )
}
