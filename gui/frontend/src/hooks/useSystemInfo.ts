import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { SystemInfo } from "../lib/api"

export function useSystemInfo() {
  const [info, setInfo] = useState<SystemInfo | null>(null)
  useEffect(() => { api.systemInfo().then(setInfo).catch(() => {}) }, [])
  return info
}
