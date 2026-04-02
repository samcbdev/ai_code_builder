from dotenv import load_dotenv
from app.core.ollama_client import OllamaClient
from app.engines.codegen_sanitizer import sanitize_llm_output, RejectGeneration

load_dotenv()
# llm = OpenRouterClient(api_key=os.environ.get("OPENROUTER_API_KEY"))
llm = OllamaClient()

BASE_PROJECT_PATH = "storage/workspace"
def read_current_file(project_id: str, path: str):
    with open(f"{BASE_PROJECT_PATH}/{project_id}/{path}", "r") as f:
        return f.read()

def generate_code(blueprint: dict, project_state: dict) -> dict:
    generated = {}

    if blueprint["intent"] == "FIX_ERROR":
        for path in blueprint["allowed_actions"]["modify"]:
            current = read_current_file(project_state["project_id"], path)
            prompt = build_fix_prompt(
                path=path,
                error=project_state["runtime"]["signals"],
                current_content=current
            )
            raw = llm.generate(prompt)
            content = sanitize_llm_output(raw)
            generated[path] = {
                "content": content,
                "reason": "Fix runtime error"
            }
        
        return {"generated_files": generated}

    allowed_files = blueprint["allowed_actions"]["create"]

    for path in allowed_files:
        prompt = build_prompt(
            path=path,
            intent=blueprint["intent"],
            stack=project_state.get("stack", "Next.js + Tailwind")
        )

        try:
            raw = llm.generate(prompt)
            content = sanitize_llm_output(raw)
        except RejectGeneration:
            continue

        generated[path] = {
            "content": content,
            "reason": f"Generated for {blueprint['intent']}"
        }

    return {"generated_files": generated}

def build_prompt(path: str, intent: str, stack: str) -> str:
    return f"""
You are generating code for a single file.

File path: {path}
Intent: {intent}
Project stack: {stack}

Rules:
- Output ONLY valid code
- Do NOT use markdown
- Do NOT reference other files
- Do NOT explain anything
- Do NOT include command-line instructions
- Do NOT include shell commands
- Do NOT include inline comments that reference commands or setup steps
- Do NOT assume the existence of any external tooling
- The output MUST contain only the file’s source code content
"""

def build_fix_prompt(path: str, error: dict, current_content: str) -> str:
    return f"""
You are fixing a build/runtime error in an existing project.

Error:
{error}

File path:
{path}

Current file content:
<<<FILE_START
{current_content}
FILE_END>>>

Rules:
- Modify ONLY this file
- Make the MINIMAL change required to fix the error
- Do NOT rewrite unrelated code
- Do NOT add explanations
- Output ONLY valid code
- Do NOT use markdown
- Do NOT include command-line instructions
- Do NOT include shell commands
- Do NOT reference other files
- Do NOT include comments about setup, build, or commands
"""