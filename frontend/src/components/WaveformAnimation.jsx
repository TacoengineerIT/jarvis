/* Animated waveform bars — shown during RECORDING and SPEAKING states */
const HEIGHTS = [12, 20, 32, 24, 16, 28, 20, 14]
const DELAYS   = [0, 0.1, 0.2, 0.15, 0.25, 0.05, 0.3, 0.2]

export default function WaveformAnimation({ active = true, color = 'bg-tertiary' }) {
  return (
    <div className="flex items-end gap-[3px] h-8">
      {HEIGHTS.map((h, i) => (
        <div
          key={i}
          className={`w-[3px] ${color} rounded-full ${active ? 'waveform-bar' : 'opacity-20'}`}
          style={{
            height: `${h}px`,
            animationDelay: `${DELAYS[i]}s`,
            animationDuration: `${0.8 + (i % 3) * 0.15}s`,
          }}
        />
      ))}
    </div>
  )
}
