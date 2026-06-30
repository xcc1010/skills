---
name: example-echo
description: Echoes the user's input back verbatim. Use only to verify end-to-end that skill loading, the catalog, and the lint pipeline work — not for real tasks.
version: 0.1.0
owner: platform-team
tags: [example, smoke-test]
allowed-tools: []
---

# Example: Echo

A minimal, harmless worked example so the repo has at least one valid skill the
catalog and linter can operate on.

## When to use

Only as a smoke test of the SkillHub pipeline. Delete it once you have real skills.

## Instructions

Repeat the user's message back to them, unchanged, prefixed with `echo: `.
