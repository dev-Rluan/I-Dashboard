import { useEffect, useRef } from "react"

export function useInterval(cb: () => void, ms: number) {
  const cbRef = useRef(cb)
  useEffect(() => { cbRef.current = cb })
  useEffect(() => {
    const id = setInterval(() => cbRef.current(), ms)
    return () => clearInterval(id)
  }, [ms])
}
