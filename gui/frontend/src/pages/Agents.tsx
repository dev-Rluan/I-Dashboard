import { useState, useEffect } from "react"
import { api } from "../lib/api"
import type { Agent, AgentSnapshot, Resources } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import StatusBadge from "../components/StatusBadge"

function fmt(bytes: number) {
  if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + " GB"
  if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + " MB"
  return (bytes / 1e3).toFixed(0) + " KB"
}

function PctBar({ value, warn = 70, danger = 90 }: { value: number; warn?: number; danger?: number }) {
  const color = value >= danger ? "bg-red-500" : value >= warn ? "bg-yellow-500" : "bg-cyan-500"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-10 text-right">{value.toFixed(1)}%</span>
    </div>
  )
}

function isOnline(last_seen: string) {
  const diff = Date.now() - new Date(last_seen).getTime()
  return diff < 30_000
}

function AgentDetail({ agent }: { agent: Agent }) {
  const [snap, setSnap] = useState<AgentSnapshot | null>(null)

  useEffect(() => {
    api.agentLatest(agent.id).then(setSnap).catch(() => {})
  }, [agent.id])
  useInterval(() => {
    api.agentLatest(agent.id).then(setSnap).catch(() => {})
  }, 5000)

  const res: Resources | undefined = snap?.resources ?? undefined

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-gray-100 font-medium">{agent.name}</span>
          <span className="text-gray-500 text-xs ml-2">{agent.ip}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 text-xs font-mono">{agent.os}</span>
          <StatusBadge status={isOnline(agent.last_seen) ? "active" : "inactive"} />
        </div>
      </div>

      {res ? (
        <div className="space-y-2">
          <div>
            <div className="text-gray-500 text-xs mb-1">CPU</div>
            <PctBar value={res.cpu.percent} />
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">
              메모리 ({fmt(res.memory.used)} / {fmt(res.memory.total)})
            </div>
            <PctBar value={res.memory.percent} />
          </div>
          {res.disks[0] && (
            <div>
              <div className="text-gray-500 text-xs mb-1">
                디스크 {res.disks[0].mountpoint} ({fmt(res.disks[0].used)} / {fmt(res.disks[0].total)})
              </div>
              <PctBar value={res.disks[0].percent} />
            </div>
          )}
          <div className="flex gap-4 pt-1 text-xs text-gray-500">
            <span>포트 {snap?.ports?.length ?? 0}개 열림</span>
            <span>프로세스 {snap?.processes?.length ?? 0}개</span>
            <span>서비스 {snap?.services?.length ?? 0}개</span>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-sm">스냅샷 로딩 중...</div>
      )}

      {snap && (
        <div className="text-gray-600 text-xs">
          마지막 수신: {new Date(snap._timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])

  const load = () => api.agents().then(setAgents).catch(() => {})
  useEffect(() => { load() }, [])
  useInterval(load, 10000)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">에이전트</h1>
        <span className="text-gray-500 text-sm">{agents.length}대 등록됨</span>
      </div>

      {agents.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center text-gray-500">
          <div className="text-2xl mb-2">📡</div>
          <div className="font-medium mb-1">연결된 에이전트 없음</div>
          <div className="text-xs text-gray-600">
            모니터링할 서버에서 <span className="font-mono text-gray-400">python agent/main.py</span> 를 실행하세요
          </div>
          <div className="mt-3 text-xs text-gray-600 font-mono bg-gray-900 rounded p-3 text-left">
            BACKEND_URL=http://이-서버-IP:8000{"\n"}
            AGENT_TOKEN=설정한-토큰{"\n"}
            python agent/main.py
          </div>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 xl:grid-cols-2">
          {agents.map(a => <AgentDetail key={a.id} agent={a} />)}
        </div>
      )}
    </div>
  )
}
