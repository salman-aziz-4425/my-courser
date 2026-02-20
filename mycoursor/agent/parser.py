import re
from dataclasses import dataclass


@dataclass
class EditBlock:
    file_path: str
    original: str
    updated: str


EDIT_PATTERN = re.compile(
    r"```edit\s*\n"
    r"FILE:\s*(.+?)\s*\n"
    r"<<<<<<< ORIGINAL\s*\n"
    r"(.*?)"
    r"=======\s*\n"
    r"(.*?)"
    r">>>>>>> UPDATED\s*\n?"
    r"```",
    re.DOTALL,
)


def parse_edit_blocks(response: str) -> list[EditBlock]:
    blocks: list[EditBlock] = []
    for match in EDIT_PATTERN.finditer(response):
        file_path = match.group(1).strip()
        original = match.group(2)
        updated = match.group(3)
        blocks.append(EditBlock(
            file_path=file_path,
            original=original,
            updated=updated,
        ))
    return blocks


def format_edit_summary(blocks: list[EditBlock]) -> str:
    if not blocks:
        return "No edit blocks found in the response."

    lines: list[str] = [f"Found {len(blocks)} edit block(s):\n"]
    for i, block in enumerate(blocks, 1):
        is_new = not block.original.strip()
        action = "CREATE" if is_new else "MODIFY"
        orig_lines = len(block.original.splitlines()) if block.original.strip() else 0
        new_lines = len(block.updated.splitlines())
        lines.append(
            f"  {i}. [{action}] {block.file_path} "
            f"({orig_lines} lines -> {new_lines} lines)"
        )
    return "\n".join(lines)
