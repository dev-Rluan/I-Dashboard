"""I-Dashboard Agent — 시스템 정보를 수집해 백엔드로 푸시한다.

환경변수:
  BACKEND_URL    백엔드 주소 (필수)  예: http://192.168.1.10:8000
  AGENT_TOKEN    인증 토큰           백엔드와 동일하게 설정
  AGENT_NAME     에이전트 식별자     기본값: 호스트명
  PUSH_INTERVAL  푸시 주기(초)       기본값: 5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
import platform
import socket
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "")
AGENT_NAME = os.getenv("AGENT_NAME", "") or socket.gethostname()
PUSH_INTERVAL = max(1, int(os.getenv("PUSH_INTERVAL", "5")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("agent")


def _safe(fn, fallback=None, name=""):
    try:
        return fn()
    except Exception as e:
        if name:
            log.warning("수집 실패 [%s]: %s", name, e)
        return fallback


def collect() -> dict:
    snapshot: dict = {
        "agent_id": AGENT_NAME,
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
    }

    snapshot["resources"] = _safe(lambda: __import__("core.resources", fromlist=["get_resources"]).get_resources(), name="resources")
    snapshot["network"]   = _safe(lambda: __import__("core.network",    fromlist=["get_interfaces"]).get_interfaces(),   [], name="network")
    snapshot["ports"]     = _safe(lambda: __import__("core.ports",      fromlist=["get_open_ports"]).get_open_ports(),   [], name="ports")
    snapshot["processes"] = _safe(lambda: __import__("core.processes",  fromlist=["get_processes"]).get_processes(),     [], name="processes")
    snapshot["services"]  = _safe(lambda: __import__("core.services",   fromlist=["get_services"]).get_services(),       [], name="services")
    snapshot["firewall"]  = _safe(lambda: __import__("core.firewall",   fromlist=["get_firewall_status"]).get_firewall_status(), name="firewall")
    snapshot["docker"]    = _safe(
        lambda: __import__("core.docker", fromlist=["get_containers"]).get_containers(),
        {"supported": False, "containers": []},
        name="docker",
    )

    return snapshot


def push(snapshot: dict) -> bool:
    body = json.dumps(snapshot).encode()
    req = urllib.request.Request(
        f"{BACKEND_URL}/api/agents/report",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Agent-Token": AGENT_TOKEN,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        log.warning("Push rejected: HTTP %d", e.code)
    except Exception as e:
        log.warning("Push failed: %s", e)
    return False


def run() -> None:
    if not BACKEND_URL:
        log.error("BACKEND_URL이 설정되지 않았습니다. .env 또는 환경변수를 확인하세요.")
        sys.exit(1)

    log.info("Agent 시작: %s → %s (간격: %ds)", AGENT_NAME, BACKEND_URL, PUSH_INTERVAL)

    while True:
        try:
            snapshot = collect()
            if push(snapshot):
                log.debug("푸시 완료")
            # push 실패 시 다음 주기에 재시도 (로그는 push 내부에서 출력)
        except Exception as e:
            log.error("수집 오류: %s", e)
        time.sleep(PUSH_INTERVAL)


if __name__ == "__main__":
    run()
