"""Shared helpers for the SkillHub tooling (step 1: skills as code).

Zero-install by design: uses PyYAML if it happens to be available, otherwise
falls back to a minimal parser that understands the constrained frontmatter the
shipped template uses (scalars + inline lists like `tags: [a, b]`).

When you adopt your real internal skill spec, this is one of the two swap
points: point `parse_frontmatter` / the schema at your format and the rest of
the pipeline follows.
"""

from __future__ import annotations

import os
from typing import Iterator, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")

# --- frontmatter loading ----------------------------------------------------

try:  # full YAML if the environment has it
    import yaml  # type: ignore

    def _load_yaml(text: str) -> dict:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("frontmatter is not a mapping")
        return data

except ModuleNotFoundError:  # zero-dependency fallback

    def _load_yaml(text: str) -> dict:
        data: dict = {}
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                data[key] = (
                    [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
                    if inner
                    else []
                )
            elif val == "":
                data[key] = ""
            else:
                data[key] = val.strip("\"'")
        return data


def parse_frontmatter(path: str) -> Tuple[dict, str]:
    """Return (metadata, body). Raises ValueError if frontmatter is missing."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        raise ValueError("missing YAML frontmatter (file must start with '---')")
    # split on the first two '---' fences
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("frontmatter is not closed with a second '---'")
    meta = _load_yaml(parts[1])
    body = parts[2].lstrip("\n")
    return meta, body


# --- discovery --------------------------------------------------------------

def iter_skills() -> Iterator[Tuple[str, str]]:
    """Yield (dir_name, SKILL.md path) for every skill directory.

    Directories whose name starts with '_' (e.g. _template) are skipped.
    """
    if not os.path.isdir(SKILLS_DIR):
        return
    for name in sorted(os.listdir(SKILLS_DIR)):
        if name.startswith("_") or name.startswith("."):
            continue
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if os.path.isfile(skill_md):
            yield name, skill_md


def rel(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
