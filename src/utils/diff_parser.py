def parse_diff(raw_diff: str) -> list[dict]:
    results = []
    for chunk in raw_diff.split("diff --git"):
        first_line = chunk.split("\n")[0]
        if first_line.endswith(".py"):
            file_path = first_line.split(" ")[2].removeprefix("b/")
            
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

            results.append({
                "file": file_path,
                "added_lines": added_lines,
                "context": context_lines
            })
    return results


def format_for_prompt(chunk:dict) -> str:
    added = "\n".join(chunk["added_lines"])
    context = "\n".join(chunk["context"])

    return f"""file: {chunk["file"]}

Changed code:
{added}

Surrounding context:
{context}
"""


if __name__ == "__main__":
    parse_diff()
