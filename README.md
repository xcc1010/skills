# SkillHub

Internal hub for **skills** — the reusable instruction/resource assets that our
agent **harness** loads at runtime.

> Mental model: **harness** = runtime framework · **SkillHub** = data hosting ·
> **skill** = data asset.

This repository is **Step 1 — skills as code**: skills live in git, are reviewed
via PR, versioned with semver, and validated by CI. No bespoke platform yet. The
hub grows into one only when discovery / distribution / observability actually
become pain points.

## Layout

```
skills/                  the assets — one folder per skill, each with a SKILL.md
  _template/             copy-me starting point (ignored by tooling)
  example-echo/          a minimal valid example
schema/skill.schema.json the skill spec  ← SWAP POINT: replace with your real spec
tools/
  skilllib.py            shared frontmatter loader (zero-dependency)
  lint.py                CI gate: validate every skill against the spec
  build_catalog.py       generate the catalog (discovery seed)
catalog/                 GENERATED — index.json + CATALOG.md (do not hand-edit)
.github/workflows/ci.yml runs lint + catalog freshness on every PR
```

## Quickstart

```
python tools/lint.py            # validate all skills
python tools/build_catalog.py   # regenerate catalog/
```

Both run on plain Python 3 with no install. See `CONTRIBUTING.md` to add a skill.

## Two swap points

1. **Skill spec** — `schema/skill.schema.json` ships a sensible default. Replace
   it with your internal skill spec and update the checks in `tools/lint.py`.
2. **Tooling language** — the tools are Python (likely matching the harness
   stack). Port them if your CI uses something else.

## Roadmap (simple → complex)

- **Step 1 — skills as code** *(this repo)*: git + PR review + lint + generated
  catalog. The floor: versioned, validated, discoverable-by-file.
- **V1 — distribution + discovery**: a resolver/client SDK so harness instances
  pull pinned skill versions; release channels (stable/canary); a search UI over
  the catalog; usage telemetry.
- **V2 — trust + governance at scale**: trust signals (usage, freshness,
  verified), ownership/rot dashboards, policy enforcement for high-risk skills,
  audit/compliance export.

Each step is added **only when its problem appears** — don't build the platform
before the demand.
