import os
import json
import shutil

def create_snapshot(project_state: dict):
    project_id = project_state["project_id"]
    project_dir = f"storage/snapshots/{project_id}"
    os.makedirs(project_dir, exist_ok=True)

    versions = [
        int(v[1:]) for v in os.listdir(project_dir)
        if v.startswith("v") and v[1:].isdigit()
    ]
    next_version = max(versions, default=0) + 1

    snap_dir = f"{project_dir}/v{next_version}"
    os.makedirs(snap_dir, exist_ok=True)

    with open(f"{snap_dir}/state.json", "w") as f:
        json.dump(project_state, f, indent=2)

    files_dir = f"{snap_dir}/files"
    os.makedirs(files_dir, exist_ok=True)

    for path in project_state.get("files", {}):
        src = f"storage/workspace/{project_id}/{path}"
        dst = f"{files_dir}/{path}"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
    
    return next_version