import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { Resources, Port, Service } from "../lib/api"
import { useWebSocket } from "../hooks/useWebSocket"
import StatCard from "../components/StatCard"
import StatusBadge from "../components/StatusBadge"
import { useInterval } from "../hooks/useInterval"

function fmt(bytes: number) {
  if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(0)} KB`
}

export default function Overview() {
  const { data: res } = useWebSocket<Resources>("/ws/resources")
  const [ports,    setPorts]    = useState<Port[]>([])
  const [services, setServices] = useState<Service[]>([])

  const loadPorts    = () => api.ports().then(setPorts).catch(() => {})
  const loadServices = () => api.services().then(setServices).catch(() => {})

  useEffect(() => { loadPorts(); loadServices() }, [])
  useInterval(loadPorts, 10000)
  useInterval(loadServices, 15000)

  const failed = services.filter(s => s.status === "failed")
  const diskPct = res?.disks[0]?.percent ?? 0

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-100">개요</h1>

      {/* 요약 카드 */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="CPU"
          value={res?.cpu.percent.toFixed(1) ?? "—"}
          unit="%"
          percent={res?.cpu.percent}
          color="cyan"
        />
        <StatCard
          label="메모리"
          value={res ? fmt(res.memory.used) : "—"}
          unit={res ? `/ ${fmt(res.memory.total)}` : ""}
          percent={res?.memory.percent}
          color="purple"
        />
        <StatCard
          label="디스크"
          value={diskPct.toFixed(1)}
          unit="%"
          percent={diskPct}
          color={diskPct > 90 ? "red" : diskPct > 70 ? "yellow" : "green"}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* 포트 요약 */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-gray-300 font-medium mb-3">열린 포트 ({ports.length}개)</div>
          <div className="flex flex-wrap gap-2">
            {ports.slice(0, 20).map(p => (
              <span key={`${p.port}-${p.protocol}`}
                className="bg-green-900 text-green-300 text-xs px-2 py-1 rounded font-mono"
              >
                {p.port}{p.service ? ` ${p.service}` : ""}
              </span>
            ))}
            {ports.length > 20 && (
              <span className="text-gray-500 text-xs py-1">+{ports.length - 20}개</span>
            )}
          </div>
        </div>

        {/* 서비스 요약 */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-gray-300 font-medium mb-3">
            서비스
            {failed.length > 0 && (
              <span className="ml-2 bg-red-900 text-red-300 text-xs px-2 py-0.5 rounded-full">
                ⚠ {failed.length}개 실패
              </span>
            )}
          </div>
          {failed.length === 0 ? (
            <div className="text-green-400 text-sm">✓ 모든 서비스 정상</div>
          ) : (
            <div className="space-y-1">
              {failed.map(s => (
                <div key={s.name} className="flex items-center gap-2">
                  <StatusBadge status="failed" />
                  <span className="text-red-300 text-sm font-mono">{s.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
