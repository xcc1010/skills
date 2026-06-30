#!/usr/bin/env python3
"""Validate every skill against the spec. CI gate for "skills as code".

Run:  python tools/lint.py

DESIGN: spec-as-data. This engine hardcodes NO field names. It validates each
skill's frontmatter against whatever schema lives in schema/skill.schema.json.
Replace that schema with your internal skill spec (kept private in your repo)
and this linter adapts automatically — you never expose the spec to anyone.

The engine enforces a small, dependency-free subset of JSON Schema:
  required, properties, type, pattern, minLength/maxLength, enum,
  items.type, minItems/maxItems

Plus two cross-file checks a schema cannot express (configurable below):
  - the identity field must equal the skill's directory name + be unique
  - no obvious hardcoded secrets
"""

from __future__ import annotations

import json
import os
import re
import sys

from skilllib import REPO_ROOT, iter_skills, parse_frontmatter, rel

# --- config: the only place that knows anything skill-specific ---------------
SCHEMA_PATH = os.path.join(REPO_ROOT, "schema", "skill.schema.json")
IDENTITY_FIELD = "name"  # field that must equal the dir name and be unique
SECRET_SCAN = True

SECRET_RES = (
    re.compile(r"(?i)(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][^'\"]{6,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


def _is_type(val, t: str) -> bool:
    return _TYPE_CHECKS.get(t, lambda v: True)(val)


def validate_against_schema(meta: dict, schema: dict, where: str) -> list[str]:
    """Generic JSON-Schema-subset validator. Knows no field names itself."""
    errs: list[str] = []

    for field in schema.get("required", []):
        if field not in meta or meta[field] in ("", None, []):
            errs.append(f"{where}: missing required field '{field}'")

    for field, spec in schema.get("properties", {}).items():
        if field not in meta:
            continue
        val = meta[field]
        t = spec.get("type")
        if t and not _is_type(val, t):
            errs.append(f"{where}: field '{field}' must be {t}")
            continue
        if t == "string":
            if "maxLength" in spec and len(val) > spec["maxLength"]:
                errs.append(f"{where}: '{field}' exceeds maxLength {spec['maxLength']}")
            if "minLength" in spec and len(val) < spec["minLength"]:
                errs.append(f"{where}: '{field}' below minLength {spec['minLength']}")
            if "pattern" in spec and not re.search(spec["pattern"], val):
                errs.append(f"{where}: '{field}' does not match pattern {spec['pattern']}")
            if "enum" in spec and val not in spec["enum"]:
                errs.append(f"{where}: '{field}' must be one of {spec['enum']}")
        elif t == "array":
            item_spec = spec.get("items")
            if isinstance(item_spec, dict) and item_spec.get("type"):
                for i, el in enumerate(val):
                    if not _is_type(el, item_spec["type"]):
                        errs.append(f"{where}: '{field}[{i}]' must be {item_spec['type']}")
            if "minItems" in spec and len(val) < spec["minItems"]:
                errs.append(f"{where}: '{field}' needs >= {spec['minItems']} items")
            if "maxItems" in spec and len(val) > spec["maxItems"]:
                errs.append(f"{where}: '{field}' allows <= {spec['maxItems']} items")
    return errs


def check_skill(dir_name: str, path: str, schema: dict, seen: dict) -> list[str]:
    where = rel(path)
    try:
        meta, _ = parse_frontmatter(path)
    except ValueError as exc:
        return [f"{where}: {exc}"]

    errs = validate_against_schema(meta, schema, where)

    ident = meta.get(IDENTITY_FIELD)
    if ident:
        if ident != dir_name:
            errs.append(
                f"{where}: '{IDENTITY_FIELD}' ({ident!r}) must equal its directory ({dir_name!r})"
            )
        key = str(ident).lower()
        if key in seen:
            errs.append(f"{where}: duplicate {IDENTITY_FIELD}, also in {seen[key]}")
        else:
            seen[key] = where

    if SECRET_SCAN:
        full = open(path, "r", encoding="utf-8").read()
        if any(p.search(full) for p in SECRET_RES):
            errs.append(f"{where}: looks like a hardcoded secret - remove it")

    return errs


def main() -> int:
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
    except FileNotFoundError:
        print(f"ERROR: spec not found at {rel(SCHEMA_PATH)} — add your skill spec there.")
        return 2

    skills = list(iter_skills())
    if not skills:
        print("no skills found under skills/ — add one from skills/_template/")
        return 0

    seen: dict = {}
    all_errs: list[str] = []
    for dir_name, path in skills:
        all_errs.extend(check_skill(dir_name, path, schema, seen))

    if all_errs:
        print(f"FAIL: {len(all_errs)} problem(s) across {len(skills)} skill(s)\n")
        for e in all_errs:
            print("  - " + e)
        return 1

    print(f"OK: {len(skills)} skill(s) passed against {rel(SCHEMA_PATH)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
