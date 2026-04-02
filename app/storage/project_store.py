from typing import Dict, List
import json
import os

BASE_PATH = "storage/projects"

class ProjectStore:
    def __init__(self):
        os.makedirs(BASE_PATH, exist_ok=True)

    def _path(self, project_id: int) -> str:
        return f"{BASE_PATH}/{project_id}.json"

    def exists(self, project_id: int) ->bool:
        return os.path.exists(self._path(project_id))

    def create(self, project_id: int) -> Dict:
        state = {
            "project_id": project_id,
            "status": "empty",
            "files": {},
            "history": [],
            "last_intent": None,
            "error_retry_count": 0
        }
        self.save(state)
        return state

    def save(self, state: Dict):
        with open(self._path(state['project_id']), "w") as f:
            json.dump(state, f, indent=2)

    def load(self, project_id: int) -> Dict:
        with open(self._path(project_id), "r") as f:
            return json.load(f)

    def list(self) -> List[str]:
        return [f.split(".")[0] for f in os.listdir(BASE_PATH) if f.endswith(".json")]
    
    def enqueue_ui_message(self, project_id: int, message: str):
        return {"will add"}