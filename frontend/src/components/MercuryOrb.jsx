import { getStateLabel } from '../hooks/useJARVIS.js'

const STATE_COLORS = {
  LISTENING:  'shadow-[0_0_40px_rgba(198,198,200,0.2)]',
  ACTIVE:     'shadow-[0_0_60px_rgba(198,198,200,0.35)]',
  RECORDING:  'shadow-[0_0_80px_rgba(255,221,121,0.35)]',
  PROCESSING: 'shadow-[0_0_80px_rgba(255,221,121,0.5)]',
  SPEAKING:   'shadow-[0_0_60px_rgba(198,198,200,0.4)]',
}

export default function MercuryOrb({ jarvisState = 'LISTENING', size = 'lg', children }) {
  const sizeCls = size === 'lg'
    ? 'w-48 h-48 lg:w-64 lg:h-64'
    : size === 'md' ? 'w-36 h-36' : 'w-24 h-24'

  const animCls = {
    LISTENING:  'orb-listening',
    ACTIVE:     'orb-listening',
    RECORDING:  'orb-recording',
    PROCESSING: 'orb-processing',
    SPEAKING:   'orb-speaking',
  }[jarvisState] || 'orb-listening'

  const glowCls = STATE_COLORS[jarvisState] || STATE_COLORS.LISTENING

  return (
    <div className="relative group cursor-pointer select-none">
      {/* Ambient glow background */}
      <div className={`absolute inset-0 mercury-orb rounded-full blur-3xl opacity-20
                       group-hover:opacity-40 transition-opacity duration-700`} />

      {/* The orb itself */}
      <div className={`${sizeCls} ${animCls} ${glowCls}
                       mercury-orb blob-effect relative flex items-center justify-center
                       border border-white/10 transition-all duration-[2000ms]
                       group-hover:scale-105`}>
        {/* Inner ring */}
        <div className="absolute inset-3 rounded-full border border-white/5" />

        {/* Content / icon */}
        {children || (
          <span
            className="material-symbols-outlined icon-filled text-white/20"
            style={{ fontSize: size === 'lg' ? 48 : 32 }}
          >
            auto_awesome
          </span>
        )}
      </div>

      {/* Satellite droplets */}
      <div className="absolute -top-3 -right-1 w-5 h-5 mercury-gradient rounded-full opacity-50 blur-[1px]" />
      <div className="absolute top-1/2 -left-6 w-3 h-3 mercury-gradient rounded-full opacity-35" />
      <div className="absolute -bottom-5 left-1/4 w-6 h-6 mercury-gradient rounded-full opacity-40 blur-[1px]" />

      {/* State label below */}
      <p className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap
                    text-[10px] uppercase tracking-[0.25em] text-on-surface-variant">
        {getStateLabel(jarvisState)}
      </p>
    </div>
  )
}
