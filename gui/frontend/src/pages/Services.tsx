import { useState, useEffect } from "react"
import { api } from "../lib/api"
import type { Service, Agent, AgentSnapshot } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import StatusBadge from "../components/StatusBadge"

export default function Services() {
  const [services,     setServices]     = useState<Service[] | null>(null)
  const [agents,       setAgents]       = useState<Agent[]>([])
  const [selectedId,   setSelectedId]   = useState<string>("")
  const [snap,         setSnap]         = useState<AgentSnapshot | null>(null)
  const [logs,         setLogs]         = useState<string[] | null>(null)
  const [logName,      setLogName]      = useState("")
  const [search,       setSearch]       = useState("")

  const loadLocal = () => api.services().then(setServices).catch(() => setServices([]))
  useEffect(() => { loadLocal() }, [])
  useInterval(loadLocal, 10000)

  useEffect(() => {
    if (services !== null && services.length === 0) {
      api.agents().then(list => {
        setAgents(list)
        if (list.length > 0 && !selectedId) setSelectedId(list[0].id)
      }).catch(() => {})
    }
  }, [services])

  useEffect(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, [selectedId])
  useInterval(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, 10000)

  const isAgent = services !== null && services.length === 0 && agents.length > 0
  const rows: Service[] = isAgent ? (snap?.services ?? []) : (services ?? [])

  const failed  = rows.filter(s => s.status === "failed")
  const others  = rows.filter(s => s.status !== "failed")
  const visible = [...failed, ...others].filter(s => {
    if (!search) return true
    const q = search.toLowerCase()
    return s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q)
  })

  const openLogs = (name: string) => {
    setLogName(name)
    setLogs(null)
    if (!isAgent) {
      api.serviceLogs(name).then(r => setLogs(r.lines)).catch(() => setLogs(["로그를 불러올 수 없습니다."]))
    } else {
      setLogs(["에이전트 서비스 로그는 지원되지 않습니다."])
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">
          서비스
          {failed.length > 0 && (
            <span className="ml-2 bg-red-900 text-red-300 text-xs px-2 py-0.5 rounded-full">⚠ {failed.length}개 실패</span>
          )}
        </h1>
        <div className="flex items-center gap-2">
          {isAgent && (
            <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
              className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500">
              {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.ip})</option>)}
            </select>
          )}
          <input type="text" placeholder="이름·설명 검색" value={search} onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-3 py-1.5 w-48 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {isAgent && (
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-4 py-2 text-blue-300 text-xs">
          에이전트 데이터 기준 — 백엔드가 Docker 환경이므로 호스트 서비스를 직접 수집할 수 없습니다.
        </div>
      )}

      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-left">
              <th className="px-4 py-3 font-medium">서비스</th>
              <th className="px-4 py-3 font-medium">상태</th>
              <th className="px-4 py-3 font-medium">활성화</th>
              <th className="px-4 py-3 font-medium">설명</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {visible.map(s => (
              <tr key={s.name} className={`border-b border-gray-700 hover:bg-gray-750 transition-colors ${s.status === "failed" ? "bg-red-950" : ""}`}>
                <td className="px-4 py-2 font-mono text-gray-200">{s.name}</td>
                <td className="px-4 py-2"><StatusBadge status={s.status} /></td>
                <td className="px-4 py-2">
                  <span className={`text-xs ${s.enabled ? "text-green-400" : "text-gray-500"}`}>{s.enabled ? "예" : "아니오"}</span>
                </td>
                <td className="px-4 py-2 text-gray-400 truncate max-w-xs">{s.description || "—"}</td>
                <td className="px-4 py-2">
                  <button onClick={() => openLogs(s.name)}
                    className="text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-800 hover:border-cyan-600 px-2 py-0.5 rounded transition-colors">
                    로그
                  </button>
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                {services === null ? "로딩 중..." : "결과 없음"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {logName && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50" onClick={() => setLogName("")}>
          <div className="bg-gray-900 border border-gray-600 rounded-lg w-3/4 max-h-96 overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <span className="text-gray-200 font-mono">{logName} 로그</span>
              <button onClick={() => setLogName("")} className="text-gray-500 hover:text-gray-300">✕</button>
            </div>
            <div className="overflow-y-auto p-4 font-mono text-xs text-gray-300 space-y-0.5">
              {logs === null ? <div className="text-gray-500">로딩 중...</div>
                : logs.map((line, i) => (
                  <div key={i} className={
                    line.toUpperCase().includes("ERROR") ? "text-red-400" :
                    line.toUpperCase().includes("WARN")  ? "text-yellow-400" : ""
                  }>{line}</div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
