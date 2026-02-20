import os
import shutil
from dataclasses import dataclass

from mycoursor.agent.parser import EditBlock


@dataclass
class ApplyResult:
    file_path: str
    success: bool
    action: str
    message: str


def apply_edit(block: EditBlock, dry_run: bool = False) -> ApplyResult:
    is_new_file = not block.original.strip()

    if is_new_file:
        return _create_file(block, dry_run)
    else:
        return _modify_file(block, dry_run)


def _create_file(block: EditBlock, dry_run: bool) -> ApplyResult:
    if os.path.exists(block.file_path) and not block.original.strip():
        if dry_run:
            return ApplyResult(
                file_path=block.file_path,
                success=True,
                action="CREATE (overwrite)",
                message=f"Would overwrite {block.file_path}",
            )
        dir_path = os.path.dirname(block.file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(block.file_path, "w", encoding="utf-8") as f:
            f.write(block.updated)
        return ApplyResult(
            file_path=block.file_path,
            success=True,
            action="CREATE (overwrite)",
            message=f"Overwrote {block.file_path}",
        )

    if dry_run:
        return ApplyResult(
            file_path=block.file_path,
            success=True,
            action="CREATE",
            message=f"Would create {block.file_path}",
        )

    dir_path = os.path.dirname(block.file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(block.file_path, "w", encoding="utf-8") as f:
        f.write(block.updated)
    return ApplyResult(
        file_path=block.file_path,
        success=True,
        action="CREATE",
        message=f"Created {block.file_path}",
    )


def _modify_file(block: EditBlock, dry_run: bool) -> ApplyResult:
    if not os.path.exists(block.file_path):
        return ApplyResult(
            file_path=block.file_path,
            success=False,
            action="MODIFY",
            message=f"File not found: {block.file_path}",
        )

    try:
        with open(block.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return ApplyResult(
            file_path=block.file_path,
            success=False,
            action="MODIFY",
            message=f"Cannot read {block.file_path}: {e}",
        )

    if block.original not in content:
        stripped_original = block.original.strip()
        lines = content.splitlines(keepends=True)
        stripped_lines = [l.strip() for l in lines]
        stripped_target = stripped_original.splitlines()

        found = False
        for i in range(len(stripped_lines) - len(stripped_target) + 1):
            if stripped_lines[i : i + len(stripped_target)] == stripped_target:
                actual_original = "".join(lines[i : i + len(stripped_target)])
                content = content.replace(actual_original, block.updated, 1)
                found = True
                break

        if not found:
            return ApplyResult(
                file_path=block.file_path,
                success=False,
                action="MODIFY",
                message=f"Original code block not found in {block.file_path}",
            )
    else:
        content = content.replace(block.original, block.updated, 1)

    if dry_run:
        return ApplyResult(
            file_path=block.file_path,
            success=True,
            action="MODIFY",
            message=f"Would modify {block.file_path}",
        )

    backup_path = block.file_path + ".bak"
    shutil.copy2(block.file_path, backup_path)

    with open(block.file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return ApplyResult(
        file_path=block.file_path,
        success=True,
        action="MODIFY",
        message=f"Modified {block.file_path} (backup at {backup_path})",
    )


def apply_edits(blocks: list[EditBlock], dry_run: bool = False) -> list[ApplyResult]:
    return [apply_edit(block, dry_run) for block in blocks]
