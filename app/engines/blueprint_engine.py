def generate_blueprint(intent_result: dict, project_state: dict) -> dict:
    intent = intent_result["intent"]
    target = intent_result.get("target")

    if intent == "CREATE_PROJECT":
        bp = create_project_blueprint(project_state)
    
    elif intent == "FIX_ERROR":
        bp = fix_error_blueprint(intent, project_state)

    elif intent == "ADD_FEATURE":
        bp = add_feature_blueprint(intent, project_state)
    else:
        bp = no_op_blueprint("Unsupported intent", intent)
    
    return bp
        

def create_project_blueprint(project_state):
    if project_state["status"] != "empty":
        return no_op_blueprint("Project already exists", "CREATE_PROJECT")

    return {
        "type": "project_blueprint",
        "intent": "CREATE_PROJECT",
        "target": None,
        "allowed_actions": {
            "create": [
                "package.json",
                "next.config.js",
                "proxy.ts",
                "tsconfig.json",
                "postcss.config.js",
                "tailwind.config.js",

                "app/layout.tsx",
                "app/page.tsx",
                "app/globals.css",

                "public/favicon.ico"
            ],
            "modify": []
        },
        "dependencies": ["next", "react", "react-dom", "tailwindcss", "postcss", "autoprefixer"],
        "notes": "Initial Next.js 16 scaffold"
    }

def fix_error_blueprint(intent, project_state):
    runtime = project_state.get("runtime")

    if not runtime or runtime["status"] != "error":
        return no_op_blueprint("No runtime error to fix", "FIX_ERROR")

    signal = runtime["signals"][0]
    error = signal["type"]

    if error == "missing_dependency":
        return {
            "type": "project_blueprint",
            "intent": "FIX_ERROR",
            "target": 'missing_dependency',
            "allowed_actions": {
                "create": [],
                "modify": [
                    "package.json"
                ]
            },
            "dependencies": signal.get("dependencies", []),
            "notes": "Add missing dependency"
        }
    
    if error == "syntax_error":
        return {
            "type": "project_blueprint",
            "intent": "FIX_ERROR",
            "target": 'syntax_error',
            "allowed_actions": {
                "create": [],
                "modify": signal.get("files", [])
            },
            "dependencies": signal.get("dependencies", []),
            "notes": "Fix syntax error"
        }
    
    return no_op_blueprint(
        f"Unhandled runtime error: {error}",
        "FIX_ERROR"
    )

def add_feature_blueprint(intent, project_state):
    planning = project_state.get("planning")

    if not planning and planning.get("status") != "complete":
        return no_op_blueprint("planning incomplete", "ADD_FEATURE")
    
    if planning.get("feature") == "projects_crud":
        return projects_crud_blueprint(planning)

    return no_op_blueprint(
        "ADD_FEATURE not implemented yet",
        "ADD_FEATURE"
    )

def projects_crud_blueprint(planning):
    scope = planning["decisions"]["scope"]

    create, modify = [], []

    if scope in ["ui", "full_stack"]:
        create += [
            "app/projects/page.tsx",
            "app/projects/[id]/page.tsx"
        ]
    
    if scope in ["api", "full_stack"]:
        create += [
            "app/api/projects/route.ts"
        ]
    
    return {
        "type": "project_blueprint",
        "intent": "ADD_FEATURE",
        "target": "projects_crud",
        "allowed_actions": {
            "create": create,
            "modify": []
        },
        "dependencies": [],
        "notes": "Projects CRUD feature"
    }

def no_op_blueprint(reason: str, intent: str = "NO_OP"):
    return {
        "type": "project_blueprint",
        "intent": intent,
        "target": None,
        "allowed_actions": {
            "create": [],
            "modify": []
        },
        "dependencies": [],
        "notes": reason
    }