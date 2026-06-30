---
name: my-skill-name
description: One or two sentences — WHAT this skill does and WHEN to use it. The harness picks skills by this text, so be precise and concrete.
version: 0.1.0
owner: your-team
tags: [example]
allowed-tools: []
---

# <Skill title>

> Copy this folder to `skills/<your-skill-name>/`, rename it, fill in the
> frontmatter above (the `name` must equal the new folder name), then run
> `python tools/lint.py`.

## When to use

Describe the trigger conditions clearly. The model reads this to decide whether
to load the skill.

## Instructions

Step-by-step guidance the model should follow when this skill is active. Keep it
small and focused — one skill, one job.

## Resources (optional)

Reference any bundled files in this folder (scripts, templates, data) and how to
use them.
