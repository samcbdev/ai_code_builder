FEATURE_PLANS = {
    "projects_crud": {
        "required": ["fields", "auth", "scope"],
        "questions": [
            "What fields does Project have?",
            "Is authentication required? (yes/no)",
            "UI only, API only, or full stack?"
        ]
    },
    "authentication": {
        "required": ["providers", "scope"],
        "questions": [
            "Which auth providers? (credentials, google, github)",
            "Frontend only or full stack?"
        ]
    }
}

PLANNING_REQUIRED_INTENTS = {
    "ADD_FEATURE"
}

def init_planning_if_needed(intent_result: dict, state: dict):
    intent = intent_result["intent"]
    target = intent_result.get("target", None)
    
    if not planning_required(intent):
        return
    
    planning = state.get("planning")

    if planning and planning.get("status") != "none":
        return

    plan = FEATURE_PLANS.get(target)
    
    state["planning"] = {
        "status": "incomplete",
        "feature": target,
        "required": plan["required"],
        "decisions": {},
        "questions": plan["questions"]
    }

def update_planning_from_input(state:dict, user_message: str):
    planning = state.get("planning")

    if not planning and planning.get("status") != "incomplete":
        return

    extracted = extract_planning_answers(
        user_message,
        planning["required"]
    )

    planning["decisions"].update(extracted)

    if all(k in planning["decisions"] for k in planning["required"]):
        planning["status"] = "complete"

def planning_required(intent: str) -> bool:
    return intent in PLANNING_REQUIRED_INTENTS

def planning_complete(state:dict) -> bool:
    planning = state.get("planning")
    
    return bool(planning and planning.get("status") == "complete")

def extract_planning_answers(user_message: str, required: list[str]) -> dict[str, str]:
    return {
        "fields": ["name", "desc", "status"],
        "auth": true,
        "scope": "full_stack"
    }
