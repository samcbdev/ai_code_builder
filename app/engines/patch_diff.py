import difflib

def compute_unified_diff(old: str, new: str):
    return list(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            lineterm=""
        )
    )