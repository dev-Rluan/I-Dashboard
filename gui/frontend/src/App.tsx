import { BrowserRouter, Routes, Route } from "react-router-dom"
import Sidebar from "./components/Sidebar"
import Overview  from "./pages/Overview"
import Ports     from "./pages/Ports"
import Firewall  from "./pages/Firewall"
import Resources from "./pages/Resources"
import Network   from "./pages/Network"
import Processes from "./pages/Processes"
import Services  from "./pages/Services"
import Logs      from "./pages/Logs"
import Docker    from "./pages/Docker"
import Agents    from "./pages/Agents"
import { useSystemInfo } from "./hooks/useSystemInfo"

function DockerBanner({ info }: { info: ReturnType<typeof useSystemInfo> }) {
  if (!info?.is_docker) return null
  const usingHostProc = info.host_proc !== "/proc"
  return (
    <div className="bg-yellow-900/40 border-b border-yellow-700/50 px-4 py-2 text-yellow-300 text-xs flex items-center gap-2">
      <span className="font-bold">Docker 컨테이너 환경</span>
      <span className="text-yellow-500">—</span>
      <span>
        {usingHostProc
          ? "리소스·프로세스는 호스트 /proc 기준 · 방화벽·네트워크는 컨테이너 격리로 수집 불가"
          : "리소스 데이터는 컨테이너 기준 (호스트와 다를 수 있음) · 방화벽 수집 불가"}
      </span>
    </div>
  )
}

export default function App() {
  const info = useSystemInfo()
  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen bg-gray-950 text-gray-100 overflow-hidden">
        <DockerBanner info={info} />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/"          element={<Overview />}  />
              <Route path="/agents"    element={<Agents />}    />
              <Route path="/ports"     element={<Ports />}     />
              <Route path="/firewall"  element={<Firewall />}  />
              <Route path="/resources" element={<Resources />} />
              <Route path="/network"   element={<Network />}   />
              <Route path="/processes" element={<Processes />} />
              <Route path="/services"  element={<Services />}  />
              <Route path="/logs"      element={<Logs />}      />
              <Route path="/docker"    element={<Docker />}    />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
