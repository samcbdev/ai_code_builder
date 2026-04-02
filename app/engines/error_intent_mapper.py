RETRYABLE = {"build_error", "missing_file", "runtime_exception"}

def map_runtime_into_intent(runtine_result: dict) -> dict | None:
    if runtine_result["status"] != "error":
        return None

    signals = runtine_result.get("signals", [])

    for s in signals:
        if s.get("type") in RETRYABLE:
            return {
                "intent": "FIX_ERROR",
                "target": s["type"],
                "confidence": 0.9
            }

    return None