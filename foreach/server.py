from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .scanner import scan_dir
from .task_manager import TaskManager


mcp = FastMCP(
    name="foreach",
    instructions=(
        "A helper MCP server that creates and manages 'foreach' batch tasks over files.\n"
        "Create a task with a root directory and a natural-language instruction.\n"
        "Then iterate: request 'next' files, process them, and call 'done' (or 'skip').\n"
        "The server filters files using .gitignore-like rules and common noisy paths (node_modules, .env, etc.)."
    ),
)


TASKS = TaskManager()


def _rel(root: Path, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except Exception:
        return str(p)


@mcp.tool(title="Create Foreach Task")
def foreach_create_task(
    root_path: str,
    description: str,
    include_globs: Optional[List[str]] = None,
    exclude_globs: Optional[List[str]] = None,
    preview: int = 10,
) -> Dict[str, Any]:
    """Create a foreach task by scanning a directory and queuing code files.

    - root_path: directory to scan
    - description: what to do for each file (e.g., "Convert all those Python 2 files to Python 3")
    - include_globs: optional whitelist patterns
    - exclude_globs: optional extra ignore patterns
    - preview: number of files to show in the response
    """
    root = Path(root_path).resolve()
    files = scan_dir(root, include_globs=include_globs or None, exclude_globs=exclude_globs or None)
    task = TASKS.create(description=description, root=root, files=files)
    sample = files[: max(0, preview)]
    return {
        "task_id": task.id,
        "description": description,
        "root": str(root),
        "total_files": len(files),
        "preview_files": [
            {"abs": str(p), "rel": _rel(root, p)} for p in sample
        ],
        "todo": f"Task '{description}' created with {len(files)} files. Call foreach_next to get files to work on.",
    }


@mcp.tool(title="Get Next Files")
def foreach_next(task_id: int, n: int = 1) -> Dict[str, Any]:
    """Get the next N files to work on and mark them in-progress."""
    task = TASKS.get(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    items = TASKS.next_batch(task_id, n)
    return {
        "task": task.summary(),
        "files": [
            {"abs": str(it.path), "rel": _rel(task.root, it.path), "status": it.status}
            for it in items
        ],
        "todo": f"Process these {len(items)} file(s) according to: {task.description}. Then call foreach_done with the same rel or abs paths.",
    }


@mcp.tool(title="Mark Done And Suggest Next")
def foreach_done(task_id: int, files: List[str], next_n: int = 1) -> Dict[str, Any]:
    """Mark given files as done, then return task status and the next N suggestions."""
    TASKS.mark_done(task_id, files)
    task = TASKS.get(task_id)
    assert task is not None
    next_items = TASKS.next_batch(task_id, next_n)
    return {
        "task": task.summary(),
        "next_files": [
            {"abs": str(it.path), "rel": _rel(task.root, it.path), "status": it.status}
            for it in next_items
        ],
        "todo": (
            f"Marked {len(files)} as done. Process the next {len(next_items)} file(s) according to: {task.description}."
        ),
    }


@mcp.tool(title="Skip Files")
def foreach_skip(task_id: int, files: List[str]) -> Dict[str, Any]:
    """Mark given files as skipped."""
    TASKS.mark_skip(task_id, files)
    task = TASKS.get(task_id)
    assert task is not None
    return {
        "task": task.summary(),
        "todo": "Call foreach_next to continue or foreach_status to review.",
    }


@mcp.tool(title="Task Status")
def foreach_status(task_id: int, list_statuses: Optional[List[str]] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Get task summary and optionally a page of files filtered by statuses."""
    task = TASKS.get(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    files = TASKS.list_files(task_id, list_statuses)
    page = files[offset : offset + limit]
    return {
        "task": task.summary(),
        "files": [{"path": f, "rel": _rel(task.root, Path(f))} for f in page],
    }


@mcp.tool(title="Cancel Task")
def foreach_cancel(task_id: int) -> Dict[str, Any]:
    """Cancel a task (it becomes inactive)."""
    return TASKS.cancel(task_id)


def main() -> None:
    """Run the MCP server over stdio (suitable for uv/uvx and Claude Desktop)."""
    mcp.run()


if __name__ == "__main__":
    main()
