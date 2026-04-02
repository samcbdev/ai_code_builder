import os
import json
import shutil

def rollback(project_id: str, version: int):
    snap_dir = f"storage/snapshots/{project_id}/v{version}"
    if not os.path.exists(snap_dir):
        return ValueError(f"Snapshot v{version} not found for project {project_id}")
    
    with open(f"{snap_dir}/state.json", "r") as f:
        state = json.load(f)
    
    files_dir = f"{snap_dir}/files"
    print("files_dir", files_dir)
    
    for root, _, files in os.walk(files_dir):
        for file in files:
            src = os.path.join(root, file)
            rel = os.path.relpath(src, files_dir)
            dst = f"storage/workspace/{project_id}/{rel}"
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
    
    return state

# if __name__ == "__main__":
#     rollback(1, 1)