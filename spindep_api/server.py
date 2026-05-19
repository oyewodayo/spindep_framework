#!/usr/bin/env python3
# server.py  — FastAPI bridge between GUI and spindep pipeline
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, uuid, json, sys, subprocess
from pathlib import Path

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

jobs = {}   # job_id -> {status, log, results}

DATA_ROOT = Path.home() / "spindep_framework" / "spindep" / "datasets" / "normalized"
RESULTS_ROOT = Path.home() / "spindep_framework" / "spindep" / "results"



@app.get("/api/status")
def get_status():
    return {"status": "ok", "version": "1.0.0"}

    
@app.get("/api/tree")
def get_tree():
    def walk(path: Path) -> dict:
        node = {"name": path.name, "type": "folder", "children": []}
        for child in sorted(path.iterdir()):
            if child.is_dir():
                node["children"].append(walk(child))
            elif child.suffix == ".csv":
                node["children"].append({"name": child.name, "type": "file"})
        return node

    if not DATA_ROOT.exists():
        return {"name": "datasets/normalized", "type": "folder", "children": [], "error": "not found"}
    
    # Return a virtual root whose children ARE the coupling folders
    root = walk(DATA_ROOT)
    root["name"] = "datasets/normalized"   # rename for display
    return root

@app.post("/api/run")
async def run(background_tasks: BackgroundTasks, mode: str = "full"):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "log": [], "results": None}
    background_tasks.add_task(_run_pipeline, job_id, mode)
    return {"job_id": job_id}

@app.get("/api/job/{job_id}")
def get_job(job_id: str):
    j = jobs.get(job_id, {"status": "not_found"})
    return {"status": j["status"], "log": j["log"]}

@app.get("/api/results/{job_id}")
def get_results(job_id: str):
    j = jobs.get(job_id)
    if not j or not j["results"]:
        return {"error": "not ready"}
    return j["results"]

def _run_pipeline(job_id: str, mode: str):
    json_path = f"/tmp/spindep_{job_id}.json"
    try:
        import traceback
        # Add spindep/ to path so 'src' is a findable package
        spindep_root = Path.home() / "spindep_framework" / "spindep"
        if str(spindep_root) not in sys.path:
            sys.path.insert(0, str(spindep_root))

        from src.pipeline import run_pipeline

        jobs[job_id]["log"].append("[..] Starting pipeline...")
        run_pipeline(
            dataset_root=str(DATA_ROOT),
            results_root=str(RESULTS_ROOT),
            json_out=json_path,
        )
        if Path(json_path).exists():
            with open(json_path) as f:
                jobs[job_id]["results"] = json.load(f)
            jobs[job_id]["status"] = "done"
            jobs[job_id]["log"].append("[OK] Pipeline complete")
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["log"].append("[ERR] No output JSON produced")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        for line in traceback.format_exc().splitlines():
            jobs[job_id]["log"].append(f"[ERR] {line}")

#  python3 server.py --port 8001
if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)