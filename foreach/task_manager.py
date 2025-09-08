from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import itertools


@dataclass
class TaskItem:
    path: Path
    status: str = "pending"  # pending | in-progress | done | skipped | error
    error: Optional[str] = None


@dataclass
class ForeachTask:
    id: int
    description: str
    root: Path
    files: List[TaskItem] = field(default_factory=list)
    cursor: int = 0  # next index to take
    active: bool = True

    def remaining(self) -> int:
        return sum(1 for f in self.files if f.status == "pending")

    def summary(self) -> dict:
        counts = {
            "pending": 0,
            "in-progress": 0,
            "done": 0,
            "skipped": 0,
            "error": 0,
        }
        for f in self.files:
            counts[f.status] = counts.get(f.status, 0) + 1
        return {
            "id": self.id,
            "description": self.description,
            "root": str(self.root),
            "total": len(self.files),
            **counts,
        }


class TaskManager:
    def __init__(self) -> None:
        self._tasks: Dict[int, ForeachTask] = {}
        self._id_counter = itertools.count(1)

    def create(self, description: str, root: Path, files: List[Path]) -> ForeachTask:
        tid = next(self._id_counter)
        task = ForeachTask(
            id=tid,
            description=description,
            root=root,
            files=[TaskItem(path=f) for f in files],
        )
        self._tasks[tid] = task
        return task

    def get(self, task_id: int) -> Optional[ForeachTask]:
        return self._tasks.get(task_id)

    def list(self) -> List[ForeachTask]:
        return list(self._tasks.values())

    def next_batch(self, task_id: int, n: int = 1) -> List[TaskItem]:
        task = self._require(task_id)
        if not task.active:
            return []
        items: List[TaskItem] = []
        for item in task.files:
            if len(items) >= n:
                break
            if item.status == "pending":
                item.status = "in-progress"
                items.append(item)
        return items

    def mark_done(self, task_id: int, paths: List[str]) -> dict:
        task = self._require(task_id)
        count = 0
        for p in paths:
            item = self._find_item(task, Path(p))
            if item:
                item.status = "done"
                item.error = None
                count += 1
        return {"updated": count}

    def mark_skip(self, task_id: int, paths: List[str]) -> dict:
        task = self._require(task_id)
        count = 0
        for p in paths:
            item = self._find_item(task, Path(p))
            if item:
                item.status = "skipped"
                item.error = None
                count += 1
        return {"updated": count}

    def mark_error(self, task_id: int, path: str, message: str) -> dict:
        task = self._require(task_id)
        item = self._find_item(task, Path(path))
        if item:
            item.status = "error"
            item.error = message
            return {"updated": 1}
        return {"updated": 0}

    def cancel(self, task_id: int) -> dict:
        task = self._require(task_id)
        task.active = False
        return {"active": task.active}

    def status(self, task_id: int) -> dict:
        task = self._require(task_id)
        return task.summary()

    def list_files(self, task_id: int, statuses: Optional[List[str]] = None) -> List[str]:
        task = self._require(task_id)
        result: List[str] = []
        for item in task.files:
            if statuses is None or item.status in statuses:
                result.append(str(item.path))
        return result

    def _require(self, task_id: int) -> ForeachTask:
        task = self.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        return task

    @staticmethod
    def _find_item(task: ForeachTask, path: Path) -> Optional[TaskItem]:
        path = path if path.is_absolute() else (task.root / path)
        for item in task.files:
            if item.path.resolve() == path.resolve():
                return item
        return None
