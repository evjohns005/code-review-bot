CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".swift", ".kt",
}


def parse_diff(raw_diff: str) -> list[dict]:
    results = []
    for chunk in raw_diff.split("diff --git"):
        first_line = chunk.split("\n")[0]
        if not any(first_line.endswith(ext) for ext in CODE_EXTENSIONS):
            continue

        # first_line format: " a/path/to/file b/path/to/file"
        parts = first_line.split(" ")
        if len(parts) < 3:
            continue
        file_path = parts[2].removeprefix("b/")

        added_lines = []
        context_lines = []

        for line in chunk.split("\n"):
            if line.startswith("@@"):
                context_lines.append(line)
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line.removeprefix("+"))
            elif line.startswith("-") or line.startswith("---"):
                pass
            elif line.startswith(" "):
                context_lines.append(line.strip())

        if added_lines:
            results.append({
                "file": file_path,
                "added_lines": added_lines,
                "context": context_lines,
            })
    return results


def format_for_prompt(chunk: dict) -> str:
    added = "\n".join(chunk["added_lines"])
    context = "\n".join(chunk["context"])

    return f"""file: {chunk["file"]}

Changed code:
{added}

Surrounding context:
{context}
"""
