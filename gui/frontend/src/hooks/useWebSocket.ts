import { useEffect, useRef, useState } from "react"

export function useWebSocket<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws"
    const host = window.location.host
    const url = `${proto}://${host}${path}`

    function connect() {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen  = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (ev) => {
        try { setData(JSON.parse(ev.data) as T) } catch { /* ignore */ }
      }
    }

    connect()
    return () => { wsRef.current?.close() }
  }, [path])

  return { data, connected }
}
