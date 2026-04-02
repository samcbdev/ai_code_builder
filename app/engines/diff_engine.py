import os
from app.engines.patch_diff import compute_unified_diff
from app.engines.patch_apply import split_hunks, score_hunk, apply_hunk, summarize_hunks

BASE_PROJECT_PATH = "storage/workspace"

class PatchRejected(Exception):
    pass

def read_current_file(project_id: str, path: str):
    with open(f"{BASE_PROJECT_PATH}/{project_id}/{path}", "r") as f:
        return f.read()

def apply_diff(codegen_result: dict, blueprint: dict, project_state: dict) -> dict:
    patches = []

    allowed_create = set(blueprint["allowed_actions"]["create"])
    allowed_modify = set(blueprint["allowed_actions"]["modify"])

    os.makedirs(f"{BASE_PROJECT_PATH}/{project_state['project_id']}", exist_ok=True)

    for path, data in codegen_result["generated_files"].items():
        content = data["content"]
        full_path = f"{BASE_PROJECT_PATH}/{project_state['project_id']}/{path}"
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if path in allowed_create:
            if not os.path.exists(full_path):
                with open(full_path, "w") as f:
                    f.write(content)
                
                patches.append({
                    "file": path,
                    "action": "create"
                })

                project_state["files"][path] = {
                    "status": "created"
                }
        
        elif path in allowed_modify:
            if os.path.exists(full_path):
                print("inside diff engine")
                old = read_current_file(project_state["project_id"], path)
                # print("old\n", old)
                new = content
                # print("new\n", new)
                diff_lines = compute_unified_diff(old, new)
                # print("diff_lines\n", diff_lines)
                hunks = split_hunks(diff_lines)
                # print("hunks\n", hunks)

                # --- FILE LEVEL VALIDATION ---
                if len(hunks) == 0:
                    # raise PatchRejected("No changes")
                    continue

                if len(hunks) > 3:
                    # raise PatchRejected("Too many hunks")
                    continue
                
                total_adds = 0
                total_deletes = 0

                # --- HUNK LEVEL VALIDATION ---
                for hunk in hunks:
                    score = score_hunk(hunk)
                    # print("score\n", score)

                    if not score["non_ws"]:
                        # raise PatchRejected("Whitespace-only hunk")
                        continue

                    if score["total"] > 6:
                        # raise PatchRejected("Hunk too large")
                        continue

                    if score["deletes"] > 3:
                        project_state["retry"]["confidence"] -= 0.2

                    total_adds += score["adds"]
                    total_deletes += score["deletes"]

                if total_adds + total_deletes > 20:
                    # raise PatchRejected("Patch too large")
                    continue

                # --- APPLY ALL HUNKS ATOMICALLY ---
                current = old
                for hunk in hunks:
                    current = apply_hunk(current, hunk)

                with open(full_path, "w") as f:
                    f.write(current)

                patches.append({
                    "file": path,
                    "action": "modify",
                    "hunks": summarize_hunks(hunks)
                })

                project_state["files"][path] = {
                    "status": "modified"
                }
        
        else:
            patches.append({
                "file": path,
                "action": "rejected"
            })

    return {
        "patches": patches,
        "project_state": project_state
    }