import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { FirewallStatus, Agent, AgentSnapshot } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import { useSystemInfo } from "../hooks/useSystemInfo"
import StatusBadge from "../components/StatusBadge"
import UnsupportedFeature from "../components/UnsupportedFeature"

function RulesTable({ fw }: { fw: FirewallStatus }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-gray-400 text-sm">
          엔진: <span className="text-cyan-400 font-mono uppercase">{fw.engine}</span>
        </span>
        <StatusBadge status={fw.active ? "active" : "inactive"} size="md" />
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-left">
              <th className="px-4 py-3 font-medium">방향</th>
              <th className="px-4 py-3 font-medium">동작</th>
              <th className="px-4 py-3 font-medium">프로토콜</th>
              <th className="px-4 py-3 font-medium">포트</th>
              <th className="px-4 py-3 font-medium">출발지</th>
            </tr>
          </thead>
          <tbody>
            {fw.rules.map((r, i) => (
              <tr key={i} className="border-b border-gray-700 hover:bg-gray-750 transition-colors">
                <td className="px-4 py-2 text-gray-300">{r.direction}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    r.action === "allow" ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"
                  }`}>
                    {r.action === "allow" ? "허용" : "차단"}
                  </span>
                </td>
                <td className="px-4 py-2 text-gray-400 font-mono">{r.protocol}</td>
                <td className="px-4 py-2 text-cyan-300 font-mono">{r.port}</td>
                <td className="px-4 py-2 text-gray-400">{r.source}</td>
              </tr>
            ))}
            {fw.rules.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">규칙 없음</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="text-gray-500 text-xs">총 {fw.rules.length}개 규칙</div>
    </div>
  )
}

export default function Firewall() {
  const [fw, setFw] = useState<FirewallStatus | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [snap, setSnap] = useState<AgentSnapshot | null>(null)
  const sysInfo = useSystemInfo()

  const loadFw = () => api.firewall().then(setFw).catch(() => {})
  useEffect(() => { loadFw() }, [])
  useInterval(loadFw, 15000)

  useEffect(() => {
    if (fw && !fw.supported) {
      api.agents().then(list => {
        setAgents(list)
        if (list.length > 0 && !selectedId) setSelectedId(list[0].id)
      }).catch(() => {})
    }
  }, [fw])

  useEffect(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, [selectedId])

  useInterval(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, 10000)

  if (!fw) return <div className="text-gray-500 text-sm">로딩 중...</div>

  if (fw.supported) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-bold text-gray-100">방화벽 상태</h1>
        <RulesTable fw={fw} />
      </div>
    )
  }

  if (agents.length === 0) {
    const msg = sysInfo?.is_docker
      ? "Docker 컨테이너에서는 호스트 방화벽에 접근할 수 없습니다. 호스트 서버에서 에이전트를 실행하면 방화벽 정보를 확인할 수 있습니다."
      : "방화벽 정보를 수집할 수 없습니다. 관리자(root) 권한으로 실행하세요."
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-bold text-gray-100">방화벽 상태</h1>
        <UnsupportedFeature message={msg} />
      </div>
    )
  }

  const agentFw = snap?.firewall

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">방화벽 상태</h1>
        <select
          value={selectedId}
          onChange={e => setSelectedId(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500"
        >
          {agents.map(a => (
            <option key={a.id} value={a.id}>{a.name} ({a.ip})</option>
          ))}
        </select>
      </div>

      <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-4 py-2 text-blue-300 text-xs">
        에이전트 데이터 기준 — 백엔드가 Docker 환경이므로 호스트 방화벽을 직접 수집할 수 없습니다.
      </div>

      {!agentFw ? (
        <div className="text-gray-500 text-sm">에이전트 스냅샷 로딩 중...</div>
      ) : !agentFw.supported ? (
        <UnsupportedFeature message="해당 에이전트에서 방화벽 정보를 수집할 수 없습니다. root 권한이 필요하거나 방화벽이 설치되어 있지 않습니다." />
      ) : (
        <RulesTable fw={agentFw} />
      )}
    </div>
  )
}
