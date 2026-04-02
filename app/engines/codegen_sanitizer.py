import re

class RejectGeneration(Exception):
    pass

def sanitize_llm_output(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        raise RejectGeneration("Empty LLM Output")
    
    out = raw.strip()

    fence_match = re.match(r"^```[a-zA-Z]*\n([\s\S]*?)\n```$", out)
    if fence_match:
        out = fence_match.group(1).strip()
    
    banned_phrases = [
        "here is the code",
        "this code",
        "example",
        "explanation"
    ]

    lower = out.lower()
    for phrase in banned_phrases:
        if phrase in lower:
            raise RejectGeneration(f"Banned phrase detected: {phrase}")
        
    # if len(out) < 30:
    #     raise RejectGeneration("Output is too short")
    
    return out