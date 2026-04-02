import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/',          icon: 'home',             label: 'Intelligence' },
  { to: '/dashboard', icon: 'dashboard',         label: 'Dashboard'    },
  { to: '/academic',  icon: 'school',            label: 'Academic'     },
  { to: '/system',    icon: 'terminal',          label: 'System'       },
]

export default function NavigationDrawer() {
  return (
    <aside className="nav-drawer">
      {/* Logo */}
      <div className="flex flex-col items-center gap-1">
        <div className="w-10 h-10 rounded-full border border-primary/20 flex items-center justify-center overflow-hidden">
          <div className="w-full h-full bg-gradient-to-br from-primary to-primary-container rounded-full opacity-80" />
        </div>
        <span className="text-[8px] font-bold tracking-widest text-[#e2e2e4] uppercase">V4.0</span>
      </div>

      {/* Nav buttons */}
      <div className="flex flex-col items-center gap-10 flex-1">
        {NAV_ITEMS.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              isActive ? 'nav-btn-active group relative' : 'nav-btn-idle group relative'
            }
          >
            <span className="material-symbols-outlined text-2xl">{icon}</span>
            {/* Tooltip */}
            <span className="absolute left-14 bg-surface-container-high px-2 py-1 rounded text-[10px]
                             opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap
                             tracking-widest uppercase pointer-events-none z-50">
              {label}
            </span>
          </NavLink>
        ))}
      </div>

      {/* Status dot */}
      <div className="mt-auto flex flex-col items-center gap-3">
        <div className="w-1.5 h-1.5 bg-tertiary rounded-full shadow-[0_0_8px_#ffdd79]" />
        <span
          className="text-[8px] uppercase tracking-widest text-on-surface-variant"
          style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
        >
          Active
        </span>
      </div>
    </aside>
  )
}
