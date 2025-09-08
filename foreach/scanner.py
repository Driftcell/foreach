from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

try:
    from pathspec import PathSpec
    from pathspec.patterns.gitwildmatch import GitWildMatchPattern
except Exception:  # pragma: no cover - optional at import time
    PathSpec = None  # type: ignore[assignment]
    GitWildMatchPattern = None  # type: ignore[assignment]


DEFAULT_IGNORE = [
    ".git/",
    "**/.git/**",
    "**/.svn/**",
    "**/.hg/**",
    "**/.DS_Store",
    "node_modules/",
    "**/node_modules/**",
    "__pycache__/",
    "**/__pycache__/**",
    ".venv/",
    "**/.venv/**",
    "env/",
    "**/env/**",
    ".env/",
    "**/.env/**",
    "dist/",
    "build/",
    "**/*.min.js",
    "**/*.lock",
]


def load_gitignore(root: Path) -> List[str]:
    patterns: List[str] = []
    for name in [".gitignore", ".ignore"]:
        f = root / name
        if f.exists():
            try:
                patterns.extend([line.strip() for line in f.read_text().splitlines() if line.strip() and not line.strip().startswith("#")])
            except Exception:
                pass
    return patterns


def make_spec(root: Path, extra_ignores: Optional[Iterable[str]] = None):
    if PathSpec is None:
        return None
    patterns = DEFAULT_IGNORE + load_gitignore(root)
    if extra_ignores:
        patterns.extend(list(extra_ignores))
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


CODE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".m", ".mm", ".rb", ".php", ".sh", ".zsh", ".fish", ".ps1", ".sql", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".md", ".txt",
}


def is_code_file(path: Path) -> bool:
    if not path.is_file():
        return False
    ext = path.suffix.lower()
    return ext in CODE_EXTS


def scan_dir(root: Path, *, include_globs: Optional[List[str]] = None, exclude_globs: Optional[List[str]] = None) -> List[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))

    spec = make_spec(root, exclude_globs)

    results: List[Path] = []
    for p in root.rglob("*"):
        if spec and spec.match_file(str(p.relative_to(root))):
            continue
        if include_globs:
            matched = any(p.match(glob) for glob in include_globs)
            if not matched:
                # If include_globs exist, only include matching files
                continue
        if is_code_file(p):
            results.append(p)
    return results
