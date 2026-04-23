export default function UnsupportedFeature({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center h-48 text-gray-500">
      <div className="text-center">
        <div className="text-3xl mb-2">⚠</div>
        <div className="text-sm">{message ?? "이 환경에서는 지원되지 않는 기능입니다."}</div>
      </div>
    </div>
  )
}
