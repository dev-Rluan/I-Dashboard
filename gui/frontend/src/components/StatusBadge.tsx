interface Props {
  status: string
  size?: "sm" | "md"
}

const MAP: Record<string, string> = {
  open:     "bg-green-900 text-green-300",
  closed:   "bg-red-900   text-red-300",
  active:   "bg-green-900 text-green-300",
  running:  "bg-green-900 text-green-300",
  failed:   "bg-red-900   text-red-300",
  inactive: "bg-gray-700  text-gray-400",
  stopped:  "bg-gray-700  text-gray-400",
  up:       "bg-green-900 text-green-300",
  down:     "bg-red-900   text-red-300",
}

export default function StatusBadge({ status, size = "sm" }: Props) {
  const cls = MAP[status.toLowerCase()] ?? "bg-gray-700 text-gray-400"
  const sz = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
  return (
    <span className={`inline-block rounded-full font-medium ${cls} ${sz}`}>
      {status}
    </span>
  )
}
