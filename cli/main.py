"""I-Dashboard CLI — 서버 인프라 모니터링 TUI"""
import argparse
import platform
import socket
import sys
import threading
import time
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Phase별 임포트 — 모듈 없으면 None 처리
try:
    from core.ports import get_open_ports
except ImportError:
    get_open_ports = None  # type: ignore

try:
    from core.firewall import get_firewall_status
except ImportError:
    get_firewall_status = None  # type: ignore

try:
    from core.resources import get_resources
except ImportError:
    get_resources = None  # type: ignore

try:
    from core.network import get_network_interfaces
except ImportError:
    get_network_interfaces = None  # type: ignore

try:
    from core.processes import get_processes
except ImportError:
    get_processes = None  # type: ignore

try:
    from core.services import get_services
except ImportError:
    get_services = None  # type: ignore


TABS = [
    ("1", "포트"),
    ("2", "방화벽"),
    ("3", "리소스"),
    ("4", "네트워크"),
    ("5", "프로세스"),
    ("6", "서비스"),
]

HELP_TEXT = """\
[bold]I-Dashboard[/bold] — 인프라 모니터링 TUI

[bold yellow]탭 전환:[/bold yellow]
  [cyan]1[/cyan]  포트 스캐너
  [cyan]2[/cyan]  방화벽 상태
  [cyan]3[/cyan]  시스템 리소스
  [cyan]4[/cyan]  네트워크 인터페이스
  [cyan]5[/cyan]  프로세스 모니터
  [cyan]6[/cyan]  서비스 목록

[bold yellow]단축키:[/bold yellow]
  [cyan]r[/cyan]  수동 새로고침
  [cyan]q[/cyan]  종료

[bold yellow]권한:[/bold yellow]
  방화벽 수집은 관리자 권한이 필요할 수 있습니다.
  Linux/macOS: sudo python cli/main.py
  Windows: 관리자 권한 터미널에서 실행
"""


def _header(tab_id: str, refresh_at: str) -> Panel:
    hostname = socket.gethostname()
    os_name = f"{platform.system()} {platform.release()}"
    tab_line = Text()
    for tid, name in TABS:
        if tid == tab_id:
            tab_line.append(f" [{tid}]{name} ", style="bold black on cyan")
        else:
            tab_line.append(f" [{tid}]{name} ", style="dim")
        tab_line.append(" ")

    title = Text()
    title.append("I-Dashboard", style="bold cyan")
    title.append(f"  {hostname}", style="white")
    title.append(f"  {os_name}", style="dim")
    title.append(f"  갱신: {refresh_at}", style="dim")

    layout = Layout()
    layout.split_row(
        Layout(title, name="left", ratio=2),
        Layout(tab_line, name="right", ratio=3),
    )
    return Panel(layout, height=4, border_style="cyan")


# ── Tab 1: 포트 ────────────────────────────────────────────────
def _render_ports() -> Panel:
    if get_open_ports is None:
        return Panel("[red]core/ports.py 모듈 없음[/red]", title="포트 스캐너")

    ports = get_open_ports()

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("포트", style="bold", width=7)
    table.add_column("프로토콜", width=8)
    table.add_column("상태", width=8)
    table.add_column("서비스", width=14)
    table.add_column("PID", width=7)
    table.add_column("프로세스", width=20)
    table.add_column("사용자")

    for p in ports:
        state_text = Text("● 열림", style="bold green") if p["state"] == "open" else Text("○ 닫힘", style="red")
        table.add_row(
            str(p["port"]),
            p["protocol"],
            state_text,
            p.get("service") or "-",
            str(p["pid"]) if p.get("pid") else "-",
            p.get("process") or "-",
            p.get("user") or "-",
        )

    count = len(ports)
    subtitle = f"총 {count}개 포트 열림  [dim](r: 새로고침  q: 종료)[/dim]"
    return Panel(table, title="[bold]포트 스캐너[/bold]", subtitle=subtitle, border_style="green")


# ── Tab 2: 방화벽 ──────────────────────────────────────────────
def _render_firewall() -> Panel:
    if get_firewall_status is None:
        return Panel("[red]core/firewall.py 모듈 없음[/red]", title="방화벽 상태")

    fw = get_firewall_status()

    if not fw.get("supported"):
        return Panel(
            "[yellow]이 환경에서는 방화벽 정보를 수집할 수 없습니다.\n관리자 권한으로 실행하거나, 지원되는 방화벽(ufw/iptables/firewalld)이 설치되어 있는지 확인하세요.[/yellow]",
            title="방화벽 상태",
            border_style="yellow",
        )

    engine = fw.get("engine", "unknown")
    active = fw.get("active", False)
    active_badge = Text("● 활성", style="bold green") if active else Text("○ 비활성", style="bold red")

    header = Text()
    header.append(f"엔진: {engine.upper()}  ", style="bold")
    header.append("상태: ")
    header.append_text(active_badge)

    rules = fw.get("rules", [])
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("방향", width=10)
    table.add_column("동작", width=10)
    table.add_column("프로토콜", width=10)
    table.add_column("포트", width=14)
    table.add_column("출발지")

    for r in rules[:50]:
        direction = r.get("direction", "")
        action_raw = r.get("action", "")
        action_text = (
            Text("허용", style="bold green") if action_raw == "allow"
            else Text("차단", style="bold red") if action_raw in ("deny", "drop")
            else Text(action_raw, style="yellow")
        )
        table.add_row(
            direction,
            action_text,
            r.get("protocol", "any"),
            r.get("port", "any"),
            r.get("source", "any"),
        )

    content = Layout()
    content.split_column(
        Layout(header, size=1),
        Layout(table),
    )
    subtitle = f"규칙 {len(rules)}개  [dim](r: 새로고침  q: 종료)[/dim]"
    return Panel(content, title="[bold]방화벽 상태[/bold]", subtitle=subtitle, border_style="blue")


# ── Tab 3: 리소스 ──────────────────────────────────────────────
def _render_resources() -> Panel:
    if get_resources is None:
        return Panel("[dim]Phase 2에서 구현 예정[/dim]", title="시스템 리소스", border_style="dim")
    data = get_resources()
    return _build_resources_panel(data)


def _build_resources_panel(data: dict) -> Panel:
    from rich.columns import Columns

    cpu = data.get("cpu", {})
    mem = data.get("memory", {})
    swap = data.get("swap", {})
    disks = data.get("disks", [])

    def gauge(label: str, pct: float, width: int = 30) -> Text:
        filled = int(width * pct / 100)
        bar = "█" * filled + "░" * (width - filled)
        color = "green" if pct < 60 else "yellow" if pct < 85 else "red"
        t = Text()
        t.append(f"{label:<6} ", style="bold")
        t.append(f"[{bar}]", style=color)
        t.append(f" {pct:5.1f}%", style=f"bold {color}")
        return t

    lines: list[Text] = []

    # CPU
    lines.append(Text("── CPU ──────────────────────────────", style="dim"))
    lines.append(gauge("전체", cpu.get("percent", 0)))
    for i, pct in enumerate(cpu.get("per_core", [])):
        lines.append(gauge(f"코어{i}", pct, width=20))

    lines.append(Text(""))
    lines.append(Text("── 메모리 ──────────────────────────", style="dim"))
    mem_pct = mem.get("percent", 0)
    lines.append(gauge("RAM", mem_pct))
    used_gb = mem.get("used", 0) / 1024 ** 3
    total_gb = mem.get("total", 0) / 1024 ** 3
    lines.append(Text(f"       사용: {used_gb:.1f} GB / {total_gb:.1f} GB", style="dim"))

    if swap.get("total", 0):
        lines.append(gauge("스왑", swap.get("percent", 0)))

    lines.append(Text(""))
    lines.append(Text("── 디스크 ──────────────────────────", style="dim"))
    disk_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
    disk_table.add_column("마운트", width=16)
    disk_table.add_column("사용", width=8)
    disk_table.add_column("전체", width=8)
    disk_table.add_column("사용률", width=8)
    disk_table.add_column("읽기/s", width=10)
    disk_table.add_column("쓰기/s", width=10)
    for d in disks:
        pct = d.get("percent", 0)
        color = "green" if pct < 70 else "yellow" if pct < 90 else "red"
        disk_table.add_row(
            d.get("mountpoint", ""),
            f"{d.get('used', 0)/1024**3:.1f}G",
            f"{d.get('total', 0)/1024**3:.1f}G",
            Text(f"{pct:.0f}%", style=f"bold {color}"),
            f"{d.get('read_bytes_sec', 0)/1024:.0f}K",
            f"{d.get('write_bytes_sec', 0)/1024:.0f}K",
        )

    from rich.console import Group
    content = Group(*[l if isinstance(l, Text) else l for l in lines], disk_table)
    return Panel(content, title="[bold]시스템 리소스[/bold]", border_style="magenta")


# ── Tab 4: 네트워크 ────────────────────────────────────────────
def _render_network() -> Panel:
    if get_network_interfaces is None:
        return Panel("[dim]Phase 2에서 구현 예정[/dim]", title="네트워크 인터페이스", border_style="dim")

    interfaces = get_network_interfaces()
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("인터페이스", width=14)
    table.add_column("IP 주소", width=18)
    table.add_column("MAC", width=20)
    table.add_column("상태", width=8)
    table.add_column("수신/s", width=12)
    table.add_column("송신/s", width=12)
    table.add_column("에러", width=6)

    for iface in interfaces:
        status_up = iface.get("status", "").lower() == "up"
        status_text = Text("● UP", style="bold green") if status_up else Text("○ DOWN", style="red")
        rx = iface.get("bytes_recv_sec", 0)
        tx = iface.get("bytes_sent_sec", 0)
        table.add_row(
            iface.get("name", ""),
            iface.get("ip", "-"),
            iface.get("mac", "-"),
            status_text,
            _fmt_bytes(rx),
            _fmt_bytes(tx),
            str(iface.get("packets_err", 0)),
        )

    return Panel(table, title="[bold]네트워크 인터페이스[/bold]", border_style="cyan")


def _fmt_bytes(b: float) -> str:
    if b >= 1024 ** 2:
        return f"{b/1024**2:.1f} MB"
    if b >= 1024:
        return f"{b/1024:.1f} KB"
    return f"{b:.0f} B"


# ── Tab 5: 프로세스 ────────────────────────────────────────────
def _render_processes(sort_by: str = "cpu") -> Panel:
    if get_processes is None:
        return Panel("[dim]Phase 3에서 구현 예정[/dim]", title="프로세스 모니터", border_style="dim")

    procs = get_processes()
    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs = sorted(procs, key=lambda x: x.get(key, 0), reverse=True)[:20]

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("PID", width=7)
    table.add_column("프로세스", width=22)
    table.add_column("상태", width=10)
    table.add_column("CPU%", width=7)
    table.add_column("MEM%", width=7)
    table.add_column("MEM(MB)", width=9)
    table.add_column("사용자", width=12)

    for p in procs:
        status = p.get("status", "")
        st_style = "red" if status == "zombie" else "green" if status == "running" else "dim"
        table.add_row(
            str(p.get("pid", "")),
            p.get("name", "")[:20],
            Text(status, style=st_style),
            f"{p.get('cpu_percent', 0):.1f}",
            f"{p.get('memory_percent', 0):.1f}",
            f"{p.get('memory_mb', 0):.0f}",
            (p.get("user") or "")[:12],
        )

    sort_label = "CPU" if sort_by == "cpu" else "메모리"
    subtitle = f"상위 20개 ({sort_label} 정렬)  [dim](c: CPU순  m: 메모리순  q: 종료)[/dim]"
    return Panel(table, title="[bold]프로세스 모니터[/bold]", subtitle=subtitle, border_style="yellow")


# ── Tab 6: 서비스 ──────────────────────────────────────────────
def _render_services() -> Panel:
    if get_services is None:
        return Panel("[dim]Phase 3에서 구현 예정[/dim]", title="서비스 목록", border_style="dim")

    svcs = get_services()

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("서비스", width=30)
    table.add_column("상태", width=12)
    table.add_column("활성화", width=8)
    table.add_column("설명")

    failed = [s for s in svcs if s.get("status") == "failed"]
    active = [s for s in svcs if s.get("status") == "active"]
    others = [s for s in svcs if s.get("status") not in ("failed", "active")]

    for svc in failed + active + others:
        status = svc.get("status", "")
        if status == "active":
            st_text = Text("● active", style="bold green")
        elif status == "failed":
            st_text = Text("✗ failed", style="bold red")
        elif status == "running":
            st_text = Text("● running", style="bold green")
        elif status == "stopped":
            st_text = Text("○ stopped", style="dim")
        else:
            st_text = Text(f"○ {status}", style="dim")

        enabled = svc.get("enabled", False)
        enabled_text = Text("예", style="green") if enabled else Text("아니오", style="dim")

        table.add_row(
            svc.get("name", "")[:28],
            st_text,
            enabled_text,
            (svc.get("description") or "")[:60],
        )

    failed_count = len(failed)
    badge = f"  [bold red]⚠ 실패 {failed_count}개[/bold red]" if failed_count else ""
    subtitle = f"총 {len(svcs)}개{badge}  [dim](q: 종료)[/dim]"
    return Panel(table, title="[bold]서비스 목록[/bold]", subtitle=subtitle, border_style="blue")


# ── 메인 루프 ──────────────────────────────────────────────────
class Dashboard:
    def __init__(self, refresh: int = 5):
        self.tab = "1"
        self.refresh = refresh
        self.sort_by = "cpu"
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def _build(self) -> Layout:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
        )
        layout["header"].update(_header(self.tab, now))
        layout["body"].update(self._render_tab())
        return layout

    def _render_tab(self):
        if self.tab == "1":
            return _render_ports()
        if self.tab == "2":
            return _render_firewall()
        if self.tab == "3":
            return _render_resources()
        if self.tab == "4":
            return _render_network()
        if self.tab == "5":
            return _render_processes(self.sort_by)
        if self.tab == "6":
            return _render_services()
        return Panel("", title="")

    def _input_thread(self, live: "Live"):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while not self._stop.is_set():
                ch = sys.stdin.read(1)
                with self._lock:
                    if ch in ("q", "Q"):
                        self._stop.set()
                    elif ch in ("1", "2", "3", "4", "5", "6"):
                        self.tab = ch
                    elif ch in ("r", "R"):
                        pass  # 다음 루프에서 자동 갱신
                    elif ch in ("c", "C"):
                        self.sort_by = "cpu"
                    elif ch in ("m", "M"):
                        self.sort_by = "memory"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def run(self):
        console = Console()

        # Windows에서는 raw 모드 미지원 → 타이머만 사용
        use_input_thread = sys.platform != "win32"

        with Live(self._build(), console=console, refresh_per_second=1, screen=True) as live:
            if use_input_thread:
                t = threading.Thread(target=self._input_thread, args=(live,), daemon=True)
                t.start()

            last = time.time()
            while not self._stop.is_set():
                if time.time() - last >= self.refresh:
                    with self._lock:
                        live.update(self._build())
                    last = time.time()
                else:
                    live.update(self._build())
                time.sleep(0.5)

                if not use_input_thread:
                    # Windows: 키 입력 없이 종료 불가 → Ctrl+C만 지원
                    pass


def main():
    parser = argparse.ArgumentParser(
        prog="idashboard",
        description="I-Dashboard — 서버 인프라 모니터링 TUI",
    )
    parser.add_argument(
        "--refresh", "-r", type=int, default=5, metavar="초",
        help="자동 갱신 주기 (기본: 5초)",
    )
    parser.add_argument(
        "--tab", "-t", choices=["1", "2", "3", "4", "5", "6"], default="1",
        help="시작 탭 (기본: 1=포트)",
    )
    args = parser.parse_args()

    dash = Dashboard(refresh=args.refresh)
    dash.tab = args.tab

    try:
        dash.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
