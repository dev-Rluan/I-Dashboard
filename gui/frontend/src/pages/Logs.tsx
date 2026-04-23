import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { LogEntry } from "../lib/api"

export default function Logs() {
  const [logs,    setLogs]    = useState<LogEntry[]>([])
  const [logType, setLogType] = useState<"system" | "auth">("system")
  const [search,  setSearch]  = useState("")

  useEffect(() => {
    api.logs(logType, 200).then(setLogs).catch(() => setLogs([]))
  }, [logType])

  const visible = search
    ? logs.filter(l => l.raw.toLowerCase().includes(search.toLowerCase()))
    : logs

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">로그 뷰어</h1>
        <div className="flex gap-2">
          <input type="text" placeholder="키워드 검색"
            value={search} onChange={e => setSearch(e.target.value)}
            className="bg-gray-800 border border-gray-600 text-gray-200 text-sm rounded px-3 py-1.5 w-48 focus:outline-none focus:border-cyan-500"
          />
          {(["system", "auth"] as const).map(t => (
            <button key={t} onClick={() => setLogType(t)}
              className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                logType === t ? "bg-cyan-700 border-cyan-500 text-white" : "bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400"
              }`}
            >
              {t === "system" ? "시스템" : "인증"}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 h-[calc(100vh-220px)] overflow-y-auto font-mono text-xs space-y-0.5">
        {visible.map((l, i) => (
          <div key={i} className={
            l.level === "ERROR" ? "text-red-400" :
            l.level === "WARN"  ? "text-yellow-400" :
            "text-gray-400"
          }>{l.raw}</div>
        ))}
        {visible.length === 0 && (
          <div className="text-gray-600 text-center py-8">로그 없음</div>
        )}
      </div>
      <div className="text-gray-500 text-xs">{visible.length}개 / {logs.length}개</div>
    </div>
  )
}
