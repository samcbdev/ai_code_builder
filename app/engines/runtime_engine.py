import subprocess
import subprocess
import os
import time

BASE_PROJECT_PATH = "storage/workspace"

def run_runtime(project_state: dict) -> dict:
    start = time.time()
    signals = []

    project_root = f"{BASE_PROJECT_PATH}/{project_state['project_id']}"

    for path in project_state.get("files", []):
        full_path = f"{project_root}/{path}"

        if not os.path.exists(full_path):
            signals.append({
                "type": "missing_file",
                "file": path
            })
            
    if signals:
        return _result("error", signals, start)

    is_node = os.path.exists(f"{project_root}/package.json")
    if not is_node:
        return _result("skipped", [
            {"type": "no_runtime_detected"}
        ], start)
    
    node_modules = os.path.exists(f"{project_root}/node_modules")
    if not node_modules:
        try:
            proc = subprocess.run(
                ["npm", "install"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600
            )

            if proc.returncode != 0:
                signals.append({
                    "type": "install_error",
                    "message": proc.stderr[-500:]
                })
                return _result("error", signals, start)
        
        except Exception as e:
            signals.append({
                "type": "install_exception",
                "message": str(e)
            })
            return _result("error", signals, start)      

    try:
        proc = subprocess.run(
            # ["npm", "install"],
            ["npm", "run", "build"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600
        )

        if proc.returncode != 0:
            signals.append({
                "type": "build_error",
                "message": proc.stderr[-500:]
            })
            return _result("error", signals, start)
    
    except Exception as e:
        signals.append({
            "type": "build_exception",
            "message": str(e)
        })
    
    return _result("success", [], start)

def _result(status: str, signals: list, start_time: float) -> dict:
    return {
        "status": status,
        "signals": signals,
        "duration": time.time() - start_time
    }