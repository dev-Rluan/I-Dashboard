const BASE = import.meta.env.VITE_API_BASE ?? ""

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}

export const api = {
  systemInfo:  () => get<SystemInfo>("/api/system/info"),
  agents:      () => get<Agent[]>("/api/agents"),
  agentLatest: (id: string) => get<AgentSnapshot>(`/api/agents/${encodeURIComponent(id)}/latest`),
  ports:      () => get<Port[]>("/api/ports"),
  firewall:   () => get<FirewallStatus>("/api/firewall"),
  resources:  () => get<Resources>("/api/resources"),
  network:    () => get<NetworkInterface[]>("/api/network"),
  processes:  (sort = "cpu", limit = 50) =>
    get<Process[]>(`/api/processes?sort=${sort}&limit=${limit}`),
  services:   () => get<Service[]>("/api/services"),
  serviceLogs: (name: string) =>
    get<{ name: string; lines: string[] }>(`/api/services/${encodeURIComponent(name)}/logs`),
  docker:     () => get<DockerResult>("/api/docker"),
  logs:       (logType = "system", lines = 100) =>
    get<LogEntry[]>(`/api/logs?log_type=${logType}&lines=${lines}`),
}

// ── Types ──────────────────────────────────────────────────────
export interface SystemInfo {
  hostname: string; os: string; os_version: string;
  os_release: string; architecture: string; python_version: string;
  is_docker: boolean; host_proc: string;
}

export interface Port {
  port: number; protocol: string; state: string;
  service: string; pid: number; process: string; user: string;
}

export interface FirewallRule {
  direction: string; action: string; protocol: string; port: string; source: string;
}
export interface FirewallStatus {
  supported: boolean; engine: string; active: boolean; rules: FirewallRule[];
}

export interface DiskInfo {
  mountpoint: string; device: string; total: number; used: number;
  free: number; percent: number; read_bytes_sec: number; write_bytes_sec: number;
}
export interface Resources {
  cpu: { percent: number; per_core: number[]; count: number }
  memory: { total: number; used: number; available: number; cached: number; percent: number }
  swap: { total: number; used: number; percent: number }
  disks: DiskInfo[]
}

export interface NetworkInterface {
  name: string; ip: string; mac: string; status: string;
  bytes_sent_sec: number; bytes_recv_sec: number;
  packets_err: number; packets_drop: number;
}

export interface Process {
  pid: number; name: string; status: string; cpu_percent: number;
  memory_percent: number; memory_mb: number; user: string; cmdline: string;
}

export interface Service {
  name: string; status: string; enabled: boolean; description: string;
}

export interface Container {
  id: string; name: string; image: string; status: string;
  cpu_percent: number; memory_mb: number; ports: string;
}
export interface DockerResult {
  supported: boolean; containers: Container[];
}

export interface LogEntry {
  raw: string; level: string;
}

export interface Agent {
  id: string; name: string; os: string; ip: string; last_seen: string;
}

export interface AgentSnapshot {
  agent_id: string; hostname: string; os: string; architecture: string;
  _timestamp: string;
  resources?: Resources;
  network?: NetworkInterface[];
  ports?: Port[];
  processes?: Process[];
  services?: Service[];
  firewall?: FirewallStatus;
  docker?: DockerResult;
}
