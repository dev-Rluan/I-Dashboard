import { NavLink } from "react-router-dom"
import { useSystemInfo } from "../hooks/useSystemInfo"

const NAV = [
  { to: "/",          label: "개요",         icon: "⊞" },
  { to: "/ports",     label: "포트",         icon: "⛓" },
  { to: "/firewall",  label: "방화벽",       icon: "🛡" },
  { to: "/resources", label: "리소스",       icon: "📊" },
  { to: "/network",   label: "네트워크",     icon: "🌐" },
  { to: "/processes", label: "프로세스",     icon: "⚙" },
  { to: "/services",  label: "서비스",       icon: "🔧" },
  { to: "/logs",      label: "로그",         icon: "📋" },
  { to: "/docker",    label: "도커",         icon: "🐳" },
]

export default function Sidebar() {
  const info = useSystemInfo()

  return (
    <aside className="w-48 shrink-0 bg-gray-900 border-r border-gray-700 flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <div className="text-cyan-400 font-bold text-lg">I-Dashboard</div>
        {info && (
          <div className="text-gray-400 text-xs mt-1">
            <div>{info.hostname}</div>
            <div>{info.os} {info.os_release}</div>
          </div>
        )}
      </div>
      <nav className="flex-1 p-2">
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded text-sm mb-1 transition-colors ${
                isActive
                  ? "bg-cyan-900 text-cyan-300 font-medium"
                  : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
              }`
            }
          >
            <span>{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-3 text-gray-600 text-xs border-t border-gray-700">
        q/Ctrl+C to exit CLI
      </div>
    </aside>
  )
}
