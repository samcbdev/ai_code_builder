from fastapi import APIRouter
from pydantic import BaseModel
from app.storage.project_store import ProjectStore
from app.engines.intent_engine import detect_intent
from app.engines.planning_engine import init_planning_if_needed, planning_required, planning_complete, update_planning_from_input
from app.engines.blueprint_engine import generate_blueprint, no_op_blueprint
from app.engines.codegen_engine import generate_code
from app.engines.diff_engine import apply_diff
from app.engines.runtime_engine import run_runtime
from app.engines.error_intent_mapper import map_runtime_into_intent
from app.engines.snapshot_engine import create_snapshot

router = APIRouter()
store = ProjectStore()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/{project_id}")
def chat(project_id: str, payload: ChatRequest):
    if store.exists(project_id):
        state = store.load(project_id)
    else:
        state = store.create(project_id)
    
    state["retry"] = state.get("retry", None)
    state = run_pipeline(state, payload.message)

    runtime = state["runtime"]

    mapped_intent = map_runtime_into_intent(state["runtime"])

    if mapped_intent and not state.get("retry"):
        state["retry"] = {
            "count": 0,
            "confidence": mapped_intent["confidence"],
            "last_error_type": mapped_intent["target"],
            "last_diff_size": 0
        }

    state["status"] = "initialized"
    store.save(state)
    while should_retry(state):
        state["retry"]["count"] += 1

        mapped_intent = map_runtime_into_intent(state["runtime"])
        print("mapped_intent", mapped_intent)
        if not mapped_intent:
            break

        state = run_pipeline(state, "[AUTO FIX ERROR]", is_retry=True, forced_intent=mapped_intent)
        update_confidence(state)
        store.save(state)

    return {
        "project_state": state,
        "note": "state updated"
    }

def run_pipeline(state, message, is_retry=False, forced_intent=None):
    print("step 0: message received")
    print(message)
    print("project state")
    print(state)
    print("forced_intent", forced_intent)
    if is_planning_active(state) and not forced_intent:
        intent_result = {
            "intent": "PLANNING_ANSWER",
            "confidence": 1.0
        }
    else:
        intent_result = forced_intent or detect_intent(message, state)

    state["last_intent"] = intent_result
    state["history"].append({
        "role": "user" if not is_retry else "system",
        "message": message,
        "intent": intent_result["intent"],
        "retry": state["retry"].get("count", 0) if is_retry else None
    })

    if not is_planning_active(state) and planning_required(intent_result["intent"]):
        init_planning_if_needed(intent_result, state)

    if is_planning_active(state):
        update_planning_from_input(state, message)

        if not planning_complete(state):
            state["blueprint"] = no_op_blueprint("planning incomplete", intent_result["intent"])
            return state

    print("step 1: intent detected")
    print(intent_result)

    blueprint = generate_blueprint(intent_result, state)
    state["blueprint"] = blueprint

    print("step 2: blueprint generated")
    print(blueprint)

    codegen_result = generate_code(blueprint, state)
    state["codegen_preview"] = codegen_result["generated_files"]

    print("step 3: code generated")
    print(codegen_result)

    diff_result = apply_diff(codegen_result, blueprint, state)
    state = diff_result["project_state"]
    state["last_diff"] = diff_result["patches"]

    print("step 4: diff applied")
    print(state)
    create_snapshot(state)

    runtime_result = run_runtime(state)
    state["runtime"] = runtime_result

    print("step 5: runtime executed")
    print(runtime_result)
    
    return state

def should_retry(state):
    retry = state.get("retry")
    if not retry:
        return False

    if retry["count"] >= 3:
        return False

    if retry["confidence"] < 0.4:
        return False

    if state["runtime"]["status"] != "error":
        return False

    return True

def update_confidence(state):
    retry = state["retry"]

    diff_size = len(state.get("last_diff", []))
    retry["last_diff_size"] = diff_size

    # diff-based confidence
    if diff_size == 0:
        retry["confidence"] -= 0.3
    elif diff_size <= 3:
        retry["confidence"] += 0.1
    else:
        retry["confidence"] -= 0.2

    # runtime-based confidence
    runtime = state["runtime"]
    err_type = runtime["signals"][0]["type"]

    if err_type == retry["last_error_type"]:
        retry["confidence"] -= 0.2
    else:
        retry["confidence"] -= 0.1
        retry["last_error_type"] = err_type

    # clamp
    retry["confidence"] = max(0.0, min(1.0, retry["confidence"]))

def is_planning_active(state: dict) -> bool:
    planning = state.get("planning")
    return bool(planning and planning.get("status") == "incomplete")