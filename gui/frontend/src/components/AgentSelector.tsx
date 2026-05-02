import type { Agent } from "../lib/api"

interface Props {
  agents: Agent[]
  selectedId: string
  onChange: (id: string) => void
}

export function AgentSelector({ agents, selectedId, onChange }: Props) {
  if (agents.length === 0) return null
  return (
    <select value={selectedId} onChange={e => onChange(e.target.value)}
      className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded px-3 py-1.5 focus:outline-none focus:border-cyan-500">
      {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.ip})</option>)}
    </select>
  )
}

export function AgentBanner() {
  return (
    <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-4 py-2 text-blue-300 text-xs">
      에이전트 데이터 기준 — 백엔드가 Docker 환경이므로 호스트 정보를 직접 수집할 수 없습니다.
    </div>
  )
}
