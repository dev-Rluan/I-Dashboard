import { useEffect, useState } from "react"
import { api } from "../lib/api"
import type { DockerResult } from "../lib/api"
import { useInterval } from "../hooks/useInterval"
import UnsupportedFeature from "../components/UnsupportedFeature"

export default function Docker() {
  const [result, setResult] = useState<DockerResult | null>(null)
  const load = () => api.docker().then(setResult).catch(() => {})
  useEffect(() => { load() }, [])
  useInterval(load, 5000)

  if (!result) return <div className="text-gray-500 text-sm">로딩 중...</div>
  if (!result.supported) return <UnsupportedFeature message="Docker가 설치되어 있지 않거나 접근할 수 없습니다." />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-100">도커 컨테이너 ({result.containers.length}개)</h1>
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-left">
              <th className="px-4 py-3 font-medium">이름</th>
              <th className="px-4 py-3 font-medium">이미지</th>
              <th className="px-4 py-3 font-medium">상태</th>
              <th className="px-4 py-3 font-medium">CPU%</th>
              <th className="px-4 py-3 font-medium">메모리(MB)</th>
              <th className="px-4 py-3 font-medium">포트</th>
            </tr>
          </thead>
          <tbody>
            {result.containers.map(c => (
              <tr key={c.id} className="border-b border-gray-700 hover:bg-gray-750">
                <td className="px-4 py-2 font-mono text-cyan-300">{c.name}</td>
                <td className="px-4 py-2 text-gray-400 text-xs">{c.image}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    c.status.includes("Up") ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"
                  }`}>{c.status}</span>
                </td>
                <td className="px-4 py-2 text-cyan-300 font-mono">{c.cpu_percent.toFixed(1)}</td>
                <td className="px-4 py-2 text-purple-300 font-mono">{c.memory_mb.toFixed(0)}</td>
                <td className="px-4 py-2 text-gray-400 text-xs font-mono">{c.ports || "—"}</td>
              </tr>
            ))}
            {result.containers.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">실행 중인 컨테이너 없음</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
