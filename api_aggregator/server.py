import asyncio
import sys
import time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models import AggregatedReport, FetchResult, SourceConfig
from config import load_config
from fetcher import fetch_all
from aggregator import aggregate


class ServerState:
    def __init__(self):
        self.last_report: Optional[AggregatedReport] = None
        self.start_time: float = time.time()
        self.sources: List[SourceConfig] = []
        self.config_path: str = "config.json"
        self.timeout: int = 10
        self.max_concurrent: int = 5
        self.retries: int = 3


state = ServerState()


def get_version() -> str:
    from importlib.metadata import version
    return version("api_aggregator")


async def refresh_data() -> AggregatedReport:
    sources = load_config(state.config_path)
    state.sources = sources
    
    mappings = {s.name: s.response_mapping for s in sources}
    
    results = await fetch_all(
        sources=sources,
        timeout=state.timeout,
        max_concurrent=state.max_concurrent,
        retries=state.retries
    )
    
    report = aggregate(results, mappings)
    return report


app = FastAPI(
    title="API Aggregator",
    description="Async API aggregation tool",
    version=get_version()
)


@app.on_event("startup")
async def startup_event():
    try:
        state.last_report = await refresh_data()
    except Exception as e:
        print(f"Ошибка при первоначальной загрузке данных: {e}")


@app.get("/")
async def root():
    uptime_seconds = time.time() - state.start_time
    
    return {
        "name": "API Aggregator",
        "version": get_version(),
        "uptime_seconds": uptime_seconds,
    }


@app.get("/report")
async def get_full_report():
    if state.last_report is None:
        raise HTTPException(status_code=503, detail="Data not available yet")
    
    return state.last_report.model_dump(mode="json")


@app.get("/report/{name}")
async def get_source_report(name: str):
    if state.last_report is None:
        raise HTTPException(status_code=503, detail="Data not available yet")
    
    for result in state.last_report.results:
        if result.source_name == name:
            return result.model_dump(mode="json")
    
    raise HTTPException(
        status_code=404,
        detail=f"Source '{name}' not found"
    )


@app.post("/refresh")
async def refresh_report(background_tasks: BackgroundTasks):
    async def refresh_and_update():
        try:
            new_report = await refresh_data()
            state.last_report = new_report
            print(f"[{datetime.now()}] Data refreshed successfully")
        except Exception as e:
            print(f"[{datetime.now()}] Error refreshing data: {e}")
    
    background_tasks.add_task(refresh_and_update)
    
    return {
        "status": "refreshing",
        "message": "Data refresh started in background"
    }


def run_server(
    config_path: str = "config.json",
    host: str = "127.0.0.1",
    port: int = 8000,
    timeout: int = 10,
    max_concurrent: int = 5,
    retries: int = 3
):
    
    import uvicorn
    
    state.config_path = config_path
    state.timeout = timeout
    state.max_concurrent = max_concurrent
    state.retries = retries
    
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    if result == 0:
        raise OSError(f"Port {port} is already in use")
    sock.close()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )