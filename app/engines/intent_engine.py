from numpy.core.multiarray import result_type
import json
from app.core.ollama_client import OllamaClient
from app.engines.codegen_sanitizer import sanitize_llm_output, RejectGeneration

llm = OllamaClient()

ALLOWED_INTENTS = {
    "CREATE_PROJECT",
    "ADD_FEATURE",
    "FIX_ERROR",
    "QUESTION"
}

def detect_intent(message: str, project_state: dict):
    result = try_llm_intent(message, project_state)

    if result and is_valid_intent(result):
        return result

    return rule_based_intent(message, project_state)

def try_llm_intent(message: str, project_state: dict) -> dict | None:
    prompt = build_prompt(message, project_state)
    try:
        raw = llm.generate(prompt)
        content = sanitize_llm_output(raw)
    except RejectGeneration:
        return None
    
    return content

def is_valid_intent(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
    
    if result.get("intent") not in ALLOWED_INTENTS:
        return False

    confidence = result.get("confidence")
    if not isinstance(confidence, (int, float)):
        return False
    
    return 0 <= confidence <= 1

def rule_based_intent(message: str, project_state: dict) -> dict:
    msg = message.lower()

    if project_state["status"] == "empty":
        return {"intent": "CREATE_PROJECT", "confidence": 1.0}

    if "add" in msg or "create" in msg or "make" in msg:
        return {"intent": "ADD_FEATURE", "target": "authentication", "confidence": 0.9}

    if "error" in msg or "fix" in msg:
        return {"intent": "FIX_ERROR", "confidence": 0.8}

    return {"intent": "QUESTION", "confidence": 0.6}

def build_prompt(message: str, project_state: dict) -> dict:
    runtime = project_state.get("runtime") or {}
    signals = runtime.get("signals") or []
    primary_signal = signals[0] if signals else None

    return f"""
You are an intent classification engine.

Allowed intents:
{ALLOWED_INTENTS}

Project state:
- status: "{project_state.get("status")}"
- runtime status: "{runtime.get("status", None)}"
- runtime signal: {primary_signal or None}

Message:
{message}

Rules:
- If project status is "empty", intent MUST be "CREATE_PROJECT"
- If message is "[AUTO FIX ERROR]", intent MUST be "FIX_ERROR"
- If runtime status is "error", intent MUST be "FIX_ERROR" unless the message is a pure question
- If runtime status and a runtime signal are present, target MUST be non-null
- "CREATE_PROJECT" MUST have target = null
- All other intents MUST have a non-null target
- Confidence MUST be a float between 0 and 1
- Do NOT invent new intents
- Do NOT explain anything
- Do NOT use markdown
- Output ONLY valid JSON

Target inference rules:
- If runtime status and runtime signal are present, target MUST be inferred
- Infer target using the following precedence:
  1. runtime signal source (if available)
  2. runtime signal type
  3. primary failing component implied by the signal message
- Target MUST be a short lowercase string (e.g., "build", "authentication", "dependencies")

Output format (exact):
{{
  "intent": "<ONE_ALLOWED_INTENT>",
  "target": <string_or_null>,
  "confidence": <float>
}}
"""