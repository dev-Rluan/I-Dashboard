import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { NetworkInterface } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import StatusBadge from "../components/StatusBadge"

function fmtBps(b: number) {
  if (b >= 1e6) return `${(b/1e6).toFixed(1)} MB/s`
  if (b >= 1e3) return `${(b/1e3).toFixed(1)} KB/s`
  return `${b.toFixed(0)} B/s`
}

export default function Network() {
  const [ifaces, setIfaces] = useState<NetworkInterface[]>([])
  const load = () => api.network().then(setIfaces).catch(() => {})
  useEffect(() => { load() }, [])
  useInterval(load, 3000)

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-100">네트워크 인터페이스</h1>
      <div className="grid gap-4">
        {ifaces.map(iface => (
          <div key={iface.name} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-lg font-mono font-bold text-cyan-300">{iface.name}</span>
                <StatusBadge status={iface.status} size="md" />
              </div>
              <div className="text-gray-400 text-xs">
                오류: {iface.packets_err} · 드롭: {iface.packets_drop}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">IP: </span>
                <span className="text-gray-200 font-mono">{iface.ip}</span>
              </div>
              <div>
                <span className="text-gray-500">MAC: </span>
                <span className="text-gray-400 font-mono">{iface.mac}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">↓ 수신: </span>
                <span className="text-green-400 font-mono">{fmtBps(iface.bytes_recv_sec)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">↑ 송신: </span>
                <span className="text-blue-400 font-mono">{fmtBps(iface.bytes_sent_sec)}</span>
              </div>
            </div>
          </div>
        ))}
        {ifaces.length === 0 && (
          <div className="text-center text-gray-500 py-8">인터페이스 정보 없음</div>
        )}
      </div>
    </div>
  )
}
