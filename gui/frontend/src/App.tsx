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

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/"          element={<Overview />}  />
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
    </BrowserRouter>
  )
}
