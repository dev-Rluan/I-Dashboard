import { useState, useEffect } from "react"
import { api } from "../lib/api"
import type { Agent, AgentSnapshot } from "../lib/api"
import { useInterval } from "./useInterval"
import { useSystemInfo } from "./useSystemInfo"

export function useAgentFallback(interval = 10000) {
  const sysInfo = useSystemInfo()
  const isDocker = sysInfo?.is_docker ?? false

  const [agents,     setAgents]     = useState<Agent[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [snap,       setSnap]       = useState<AgentSnapshot | null>(null)

  useEffect(() => {
    if (!isDocker) return
    api.agents().then(list => {
      setAgents(list)
      if (list.length > 0 && !selectedId) setSelectedId(list[0].id)
    }).catch(() => {})
  }, [isDocker])

  useEffect(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, [selectedId])

  useInterval(() => {
    if (selectedId) api.agentLatest(selectedId).then(setSnap).catch(() => {})
  }, interval)

  return { isDocker, agents, selectedId, setSelectedId, snap }
}
