def split_hunks(diff_lines):
    hunks = []
    current = []

    for line in diff_lines:
        if line.startswith("@@"):
            if current:
                hunks.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        hunks.append(current)

    return hunks


def score_hunk(hunk):
    adds = 0
    deletes = 0
    non_ws = False

    for line in hunk:
        if line.startswith("+") and not line.startswith("+++"):
            adds += 1
            if line.strip() != "+":
                non_ws = True
        elif line.startswith("-") and not line.startswith("---"):
            deletes += 1
            if line.strip() != "-":
                non_ws = True

    return {
        "adds": adds,
        "deletes": deletes,
        "total": adds + deletes,
        "non_ws": non_ws
    }

def apply_hunk(old: str, hunk):
    old_lines = old.splitlines(keepends=True)
    result = []
    idx = 0

    for line in hunk:
        if line.startswith(" "):
            result.append(line[1:])
            idx += 1
        elif line.startswith("+") and not line.startswith("+++"):
            result.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            idx += 1  # deletion
        # headers (@@, --- , +++) are ignored

    return "".join(result)

def summarize_hunks(hunks):
    summaries = []

    for idx, hunk in enumerate(hunks, start=1):
        adds = 0
        deletes = 0
        lines = []

        for line in hunk:
            if line.startswith("+") and not line.startswith("+++"):
                adds += 1
                lines.append(line)
            elif line.startswith("-") and not line.startswith("---"):
                deletes += 1
                lines.append(line)
            elif line.startswith(" "):
                lines.append(line)

        summaries.append({
            "index": idx,
            "adds": adds,
            "deletes": deletes,
            "lines": lines
        })

    return summaries
