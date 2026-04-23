import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gui.backend.middleware.auth import BasicAuthMiddleware
from gui.backend.routers import ports, firewall, resources, network, processes, services, system, ws, docker, logs

app = FastAPI(title="I-Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic Auth — 환경변수 둘 다 설정 시에만 활성화
_user = os.getenv("DASHBOARD_USER", "")
_pass = os.getenv("DASHBOARD_PASS", "")
if _user and _pass:
    app.add_middleware(BasicAuthMiddleware, username=_user, password=_pass)

app.include_router(system.router,    prefix="/api/system")
app.include_router(ports.router,     prefix="/api")
app.include_router(firewall.router,  prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(network.router,   prefix="/api")
app.include_router(processes.router, prefix="/api")
app.include_router(services.router,  prefix="/api")
app.include_router(docker.router,    prefix="/api")
app.include_router(logs.router,      prefix="/api")
app.include_router(ws.router)
