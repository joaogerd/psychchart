from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4


DEFAULT_WORKSPACE_DIR = Path(os.environ.get("PSYCHCHART_WORKSPACE_DIR", "workspace_data"))


@dataclass(frozen=True)
class ProjectRecord:
    id: str
    name: str
    yaml: str
    created_at: str
    updated_at: str


class WorkspaceStore:
    def __init__(self, root_dir: str | Path = DEFAULT_WORKSPACE_DIR) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[ProjectRecord]:
        projects = [self._read(path) for path in self.root_dir.glob("*.json")]
        return sorted(projects, key=lambda item: item.updated_at, reverse=True)

    def get_project(self, project_id: str) -> ProjectRecord:
        path = self._path(project_id)
        if not path.exists():
            raise KeyError(project_id)
        return self._read(path)

    def create_project(self, name: str, yaml: str) -> ProjectRecord:
        now = self._now()
        record = ProjectRecord(
            id=str(uuid4()),
            name=name.strip() or "Untitled chart",
            yaml=yaml,
            created_at=now,
            updated_at=now,
        )
        self._write(record)
        return record

    def update_project(self, project_id: str, name: str | None, yaml: str | None) -> ProjectRecord:
        current = self.get_project(project_id)
        record = ProjectRecord(
            id=current.id,
            name=(name if name is not None else current.name).strip() or current.name,
            yaml=yaml if yaml is not None else current.yaml,
            created_at=current.created_at,
            updated_at=self._now(),
        )
        self._write(record)
        return record

    def delete_project(self, project_id: str) -> None:
        path = self._path(project_id)
        if not path.exists():
            raise KeyError(project_id)
        path.unlink()

    def _path(self, project_id: str) -> Path:
        safe_id = project_id.replace("/", "").replace("..", "")
        return self.root_dir / f"{safe_id}.json"

    def _read(self, path: Path) -> ProjectRecord:
        return ProjectRecord(**json.loads(path.read_text(encoding="utf-8")))

    def _write(self, record: ProjectRecord) -> None:
        self._path(record.id).write_text(
            json.dumps(asdict(record), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
