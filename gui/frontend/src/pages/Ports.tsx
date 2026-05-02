import { useState, useEffect } from "react"
import { api } from "../lib/api"
import type { Port } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import { useAgentFallback } from "../hooks/useAgentFallback"
import { AgentSelector, AgentBanner } from "../components/AgentSelector"
import StatusBadge from "../components/StatusBadge"

export default function Ports() {
  const [localPorts, setLocalPorts] = useState<Port[]>([])
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<"all" | "open" | "well-known">("all")
  const { isDocker, agents, selectedId, setSelectedId, snap } = useAgentFallback(5000)

  const load = () => api.ports().then(setLocalPorts).catch(() => {})
  useEffect(() => { if (!isDocker) load() }, [isDocker])
  useInterval(() => { if (!isDocker) load() }, 5000)

  const ports = isDocker ? (snap?.ports ?? []) : localPorts

  const visible = ports.filter(p => {
    const q = search.toLowerCase()
    const match = !q || String(p.port).includes(q) || p.service.toLowerCase().includes(q) || p.process.toLowerCase().includes(q)
    if (!match) return false
    if (filter === "open") return p.state === "open"
    if (filter === "well-known") return p.port < 1024
    return true
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">포트 스캐너</h1>
        <div className="flex gap-2">
          {isDocker && <AgentSelector agents={agents} selectedId={selectedId} onChange={setSelectedId} />}
          <input type="text" placeholder="포트·서비스·프로세스 검색"
            value={search} onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-3 py-1.5 w-52 focus:outline-none focus:border-cyan-500"
          />
          {(["all","open","well-known"] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                filter === f ? "bg-cyan-700 border-cyan-500 text-white" : "bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400"
              }`}>
              {f === "all" ? "전체" : f === "open" ? "열림" : "Well-known"}
            </button>
          ))}
        </div>
      </div>

      {isDocker && <AgentBanner />}

      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-left">
              <th className="px-4 py-3 font-medium">포트</th>
              <th className="px-4 py-3 font-medium">프로토콜</th>
              <th className="px-4 py-3 font-medium">상태</th>
              <th className="px-4 py-3 font-medium">서비스</th>
              <th className="px-4 py-3 font-medium">PID</th>
              <th className="px-4 py-3 font-medium">프로세스</th>
              <th className="px-4 py-3 font-medium">사용자</th>
            </tr>
          </thead>
          <tbody>
            {visible.map(p => (
              <tr key={`${p.port}-${p.protocol}`} className="border-b border-gray-700 hover:bg-gray-750 transition-colors">
                <td className="px-4 py-2 font-mono text-cyan-300 font-bold">{p.port}</td>
                <td className="px-4 py-2 text-gray-400 uppercase text-xs">{p.protocol}</td>
                <td className="px-4 py-2"><StatusBadge status={p.state} /></td>
                <td className="px-4 py-2 text-gray-300">{p.service || "—"}</td>
                <td className="px-4 py-2 text-gray-400 font-mono">{p.pid || "—"}</td>
                <td className="px-4 py-2 text-gray-300">{p.process || "—"}</td>
                <td className="px-4 py-2 text-gray-400">{p.user || "—"}</td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                {isDocker && !snap ? "에이전트 연결 대기 중..." : "결과 없음"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="text-gray-500 text-xs">{visible.length}개 표시 / 전체 {ports.length}개</div>
    </div>
  )
}
