import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { LogEntry, Agent, AgentSnapshot } from "../lib/api"
import { useInterval } from "../hooks/useInterval"

export default function Logs() {
  const [logs,       setLogs]       = useState<LogEntry[] | null>(null)
  const [agents,     setAgents]     = useState<Agent[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [snap,       setSnap]       = useState<AgentSnapshot | null>(null)
  const [logType,    setLogType]    = useState<"system" | "auth">("system")
  const [search,     setSearch]     = useState("")

  const loadLocal = () =>
    api.logs(logType, 200).then(rows => setLogs(rows)).catch(() => setLogs([]))
  useEffect(() => { setLogs(null); loadLocal() }, [logType])
  useInterval(loadLocal, 30000)

  useEffect(() => {
    if (logs !== null && logs.length === 0) {
      api.agents().then(list => {
        setAgents(list)
        if (list.length > 0 && !selectedId) setSelectedId(list[0].id)
      }).catch(() => {})
    }
  }, [logs])

  useEffect(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, [selectedId])
  useInterval(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, 30000)

  const isAgent = logs !== null && logs.length === 0 && agents.length > 0
  const agentLogs: LogEntry[] = isAgent
    ? (logType === "auth" ? snap?.logs_auth ?? [] : snap?.logs_system ?? [])
    : []
  const rows = isAgent ? agentLogs : (logs ?? [])

  const visible = search
    ? rows.filter(l => l.raw.toLowerCase().includes(search.toLowerCase()))
    : rows

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">로그 뷰어</h1>
        <div className="flex gap-2 items-center">
          {isAgent && (
            <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
              className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500">
              {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.ip})</option>)}
            </select>
          )}
          <input type="text" placeholder="키워드 검색" value={search} onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-3 py-1.5 w-48 focus:outline-none focus:border-cyan-500"
          />
          {(["system", "auth"] as const).map(t => (
            <button key={t} onClick={() => setLogType(t)}
              className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                logType === t ? "bg-cyan-700 border-cyan-500 text-white" : "bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400"
              }`}>
              {t === "system" ? "시스템" : "인증"}
            </button>
          ))}
        </div>
      </div>

      {isAgent && (
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-4 py-2 text-blue-300 text-xs">
          에이전트 데이터 기준 (최근 50줄) — 백엔드가 Docker 환경이므로 호스트 로그를 직접 수집할 수 없습니다.
        </div>
      )}

      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 h-[calc(100vh-260px)] overflow-y-auto font-mono text-xs space-y-0.5">
        {logs === null ? (
          <div className="text-gray-600 text-center py-8">로딩 중...</div>
        ) : visible.length === 0 ? (
          <div className="text-gray-600 text-center py-8">로그 없음</div>
        ) : visible.map((l, i) => (
          <div key={i} className={
            l.level === "ERROR" ? "text-red-400" :
            l.level === "WARN"  ? "text-yellow-400" :
            "text-gray-400"
          }>{l.raw}</div>
        ))}
      </div>
      <div className="text-gray-500 text-xs">{visible.length}개 / {rows.length}개</div>
    </div>
  )
}
