import { useState, useEffect } from "react"
import { api } from "../lib/api"
import type { Process } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import { useAgentFallback } from "../hooks/useAgentFallback"
import { AgentSelector, AgentBanner } from "../components/AgentSelector"

export default function Processes() {
  const [localProcs, setLocalProcs] = useState<Process[]>([])
  const [sort,   setSort]   = useState<"cpu" | "memory">("cpu")
  const [search, setSearch] = useState("")
  const { isDocker, agents, selectedId, setSelectedId, snap } = useAgentFallback(5000)

  const load = () => api.processes(sort).then(setLocalProcs).catch(() => {})
  useEffect(() => { if (!isDocker) load() }, [isDocker, sort])
  useInterval(() => { if (!isDocker) load() }, 3000)

  const rawProcs = isDocker ? (snap?.processes ?? []) : localProcs
  const procs = [...rawProcs].sort((a, b) =>
    sort === "cpu" ? b.cpu_percent - a.cpu_percent : b.memory_mb - a.memory_mb
  )

  const visible = procs.filter(p => {
    if (!search) return true
    const q = search.toLowerCase()
    return p.name.toLowerCase().includes(q) || String(p.pid).includes(q) || p.user.toLowerCase().includes(q)
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">프로세스 모니터</h1>
        <div className="flex gap-2">
          {isDocker && <AgentSelector agents={agents} selectedId={selectedId} onChange={setSelectedId} />}
          <input type="text" placeholder="이름·PID·사용자 검색"
            value={search} onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-3 py-1.5 w-48 focus:outline-none focus:border-cyan-500"
          />
          {(["cpu","memory"] as const).map(s => (
            <button key={s} onClick={() => setSort(s)}
              className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                sort === s ? "bg-cyan-700 border-cyan-500 text-white" : "bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400"
              }`}>
              {s === "cpu" ? "CPU순" : "메모리순"}
            </button>
          ))}
        </div>
      </div>

      {isDocker && <AgentBanner />}

      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-left">
              <th className="px-4 py-3 font-medium">PID</th>
              <th className="px-4 py-3 font-medium">프로세스</th>
              <th className="px-4 py-3 font-medium">상태</th>
              <th className="px-4 py-3 font-medium">CPU%</th>
              <th className="px-4 py-3 font-medium">MEM%</th>
              <th className="px-4 py-3 font-medium">MEM(MB)</th>
              <th className="px-4 py-3 font-medium">사용자</th>
            </tr>
          </thead>
          <tbody>
            {visible.map(p => (
              <tr key={p.pid} className={`border-b border-gray-700 hover:bg-gray-750 transition-colors ${
                p.status === "zombie" ? "bg-red-950" : ""
              }`}>
                <td className="px-4 py-2 font-mono text-gray-400">{p.pid}</td>
                <td className="px-4 py-2 text-gray-200">{p.name}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    p.status === "running" ? "bg-green-900 text-green-300" :
                    p.status === "zombie"  ? "bg-red-900 text-red-300" :
                    "bg-gray-700 text-gray-400"
                  }`}>{p.status}</span>
                </td>
                <td className="px-4 py-2 text-cyan-300 font-mono">{p.cpu_percent.toFixed(1)}</td>
                <td className="px-4 py-2 text-purple-300 font-mono">{p.memory_percent.toFixed(1)}</td>
                <td className="px-4 py-2 text-gray-400 font-mono">{p.memory_mb.toFixed(0)}</td>
                <td className="px-4 py-2 text-gray-400">{p.user}</td>
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
      <div className="text-gray-500 text-xs">{visible.length}개 표시</div>
    </div>
  )
}
