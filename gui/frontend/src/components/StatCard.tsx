interface Props {
  label: string
  value: string | number
  unit?: string
  percent?: number
  color?: "cyan" | "green" | "yellow" | "red" | "purple"
}

const COLORS = {
  cyan:   "text-cyan-400   border-cyan-700",
  green:  "text-green-400  border-green-700",
  yellow: "text-yellow-400 border-yellow-700",
  red:    "text-red-400    border-red-700",
  purple: "text-purple-400 border-purple-700",
}

function pctColor(pct: number) {
  if (pct < 60) return "bg-green-500"
  if (pct < 85) return "bg-yellow-500"
  return "bg-red-500"
}

export default function StatCard({ label, value, unit, percent, color = "cyan" }: Props) {
  const cls = COLORS[color]
  return (
    <div className={`bg-gray-800 border rounded-lg p-4 ${cls}`}>
      <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">{label}</div>
      <div className="text-2xl font-bold">
        {value}<span className="text-sm font-normal ml-1 text-gray-400">{unit}</span>
      </div>
      {percent !== undefined && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>사용률</span><span>{percent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${pctColor(percent)}`}
              style={{ width: `${Math.min(100, percent)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
