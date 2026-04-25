import { useWebSocket } from "../hooks/useWebSocket"
import type { Resources } from "../lib/api"
import { XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts"
import { useRef, useState } from "react"

function fmt(bytes: number) {
  if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(0)} KB`
}

function PctBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>{label}</span><span>{pct.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${Math.min(100,pct)}%` }} />
      </div>
    </div>
  )
}

export default function Resources() {
  const { data: res, connected } = useWebSocket<Resources>("/ws/resources")
  const histRef = useRef<{ time: string; cpu: number }[]>([])
  const [hist, setHist] = useState<typeof histRef.current>([])

  if (res) {
    const entry = { time: new Date().toLocaleTimeString(), cpu: res.cpu.percent }
    histRef.current = [...histRef.current.slice(-30), entry]
    if (hist.length !== histRef.current.length || hist[hist.length-1]?.cpu !== entry.cpu) {
      setHist([...histRef.current])
    }
  }

  const memPct = res?.memory.percent ?? 0
  const swapPct = res?.swap.percent ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">시스템 리소스</h1>
        <span className={`text-xs px-2 py-1 rounded-full ${connected ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
          {connected ? "● 실시간" : "○ 연결 끊김"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* CPU 차트 */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-gray-300 font-medium mb-3">
            CPU <span className="text-cyan-400 font-bold">{res?.cpu.percent.toFixed(1) ?? "—"}%</span>
            <span className="text-gray-500 text-xs ml-2">{res?.cpu.count ?? "—"} 코어</span>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={hist}>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0,100]} hide />
              <Tooltip formatter={(v) => [`${Number(v).toFixed(1)}%`, "CPU"]} contentStyle={{ background:"#1f2937", border:"1px solid #374151", borderRadius:6 }} />
              <Area type="monotone" dataKey="cpu" stroke="#06b6d4" fill="#0e4a5c" strokeWidth={2} dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-2 grid grid-cols-4 gap-1">
            {res?.cpu.per_core.map((pct, i) => (
              <div key={i} className="text-xs text-center">
                <div className="text-gray-500">코어{i}</div>
                <div className={pct > 80 ? "text-red-400" : pct > 50 ? "text-yellow-400" : "text-green-400"}>
                  {pct.toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 메모리 */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-gray-300 font-medium mb-3">
            메모리 <span className="text-purple-400 font-bold">{memPct.toFixed(1)}%</span>
          </div>
          {res && (
            <>
              <PctBar label="RAM" pct={memPct} color={memPct > 85 ? "bg-red-500" : memPct > 60 ? "bg-yellow-500" : "bg-purple-500"} />
              <div className="text-xs text-gray-500 mb-3">
                사용: {fmt(res.memory.used)} / 전체: {fmt(res.memory.total)}
                {res.memory.cached > 0 && ` · 캐시: ${fmt(res.memory.cached)}`}
              </div>
              {res.swap.total > 0 && <PctBar label="스왑" pct={swapPct} color="bg-orange-500" />}
            </>
          )}
        </div>
      </div>

      {/* 디스크 */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="text-gray-300 font-medium mb-3">디스크</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 text-left border-b border-gray-700">
              <th className="pb-2 font-medium">마운트</th>
              <th className="pb-2 font-medium">장치</th>
              <th className="pb-2 font-medium">사용</th>
              <th className="pb-2 font-medium">전체</th>
              <th className="pb-2 font-medium w-32">사용률</th>
              <th className="pb-2 font-medium">읽기/s</th>
              <th className="pb-2 font-medium">쓰기/s</th>
            </tr>
          </thead>
          <tbody>
            {res?.disks.map(d => {
              const c = d.percent > 90 ? "bg-red-500" : d.percent > 70 ? "bg-yellow-500" : "bg-green-500"
              return (
                <tr key={d.mountpoint} className="border-b border-gray-700">
                  <td className="py-2 text-cyan-300 font-mono">{d.mountpoint}</td>
                  <td className="py-2 text-gray-400 text-xs">{d.device}</td>
                  <td className="py-2">{fmt(d.used)}</td>
                  <td className="py-2 text-gray-400">{fmt(d.total)}</td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                        <div className={`h-1.5 rounded-full ${c}`} style={{ width: `${d.percent}%` }} />
                      </div>
                      <span className="text-xs w-10 text-right">{d.percent.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="py-2 text-gray-400 text-xs">{fmt(d.read_bytes_sec)}/s</td>
                  <td className="py-2 text-gray-400 text-xs">{fmt(d.write_bytes_sec)}/s</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
