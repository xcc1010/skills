# Contributing a skill

The paved road. Adding a skill is a pull request — no approval board, no ticket.
Code review **is** the governance.

## Add a skill

1. Copy the template:
   ```
   cp -r skills/_template skills/<your-skill-name>
   ```
   (`<your-skill-name>` must be kebab-case and will become the skill's `name`.)
2. Edit `skills/<your-skill-name>/SKILL.md` — fill in the frontmatter and the
   instructions. The `name` field must equal the folder name.
3. Validate locally:
   ```
   python tools/lint.py
   python tools/build_catalog.py
   ```
4. Commit the skill **and** the regenerated `catalog/` files, open a PR.

## What CI checks (so reviewers don't have to)

- Required fields present, name/version well-formed, name unique
- No hardcoded secrets
- The committed catalog matches the source files

Reviewers focus on **content**: is the description accurate, is the skill small
and single-purpose, are any bundled scripts safe?

## Conventions

- **One skill, one job.** Split big skills.
- **Invest in `description`.** The harness selects skills by it; a vague
  description means the skill is effectively invisible.
- **Bump `version`** (semver) on every change.
- **Set an `owner`.** Unowned skills rot and get pruned.
- **Least privilege.** Declare only the `allowed-tools` the skill truly needs.

## Promotion (paved road, not locked gate)

Skills start local. When one proves broadly useful, "promote" it by moving it
into this shared repo. The central team curates (recommends, organizes) — it does
not gatekeep submissions.
