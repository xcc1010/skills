---
name: commit-message
description: Writes a Conventional Commits message from a staged git diff. Use when the user asks to draft, write, or improve a commit message, or before committing changes.
version: 0.1.0
owner: platform-team
tags: [git, productivity]
allowed-tools: [Bash]
---

# Commit message writer

## When to use

The user is about to commit and wants a well-formed message, or asks to draft /
rewrite one.

## Instructions

1. Read the staged changes with `git diff --cached`.
2. Pick the type: `feat | fix | refactor | docs | test | chore`.
3. Write a one-line subject: `<type>(<scope>): <imperative summary>`, <= 72 chars.
4. If non-trivial, add a body explaining **why**, wrapped at 72 columns.
5. Output only the message, ready to paste.
