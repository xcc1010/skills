#!/usr/bin/env python3
"""mini-Claude — a minimal agent harness (the "runtime") in ~180 lines.

It demonstrates the SAME architecture a real agent CLI (e.g. Claude Code) uses:

    a loop where a MODEL decides to call TOOLS, the harness EXECUTES the tools
    and feeds results back, and this repeats until the model returns a final
    answer.

It also loads a SKILL from this repo's SkillHub and injects it into the system
prompt — so you can watch **Harness + SkillHub + Skill** work together:

    Harness (this file)  ── loads ──▶  Skill (skills/<name>/SKILL.md)
         │                                served by the SkillHub catalog
         └── model ⇄ tools loop ──▶ final answer

The model backend is pluggable (see the `Model` protocol). A dependency-free
`MockModel` lets the demo run offline; swap in `OpenAICompatModel` to point at
your internal model gateway. Nothing here is Anthropic's proprietary code — it
is a from-scratch teaching harness.

Run:  python harness/mini_claude.py
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable, Protocol

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- tools ------
@dataclass
class Tool:
    name: str
    description: str
    run: Callable[[dict], str]


class Registry:
    """Holds the tools the harness can execute on the model's behalf."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def add(self, tool: Tool):
        self._tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def run(self, name: str, args: dict) -> str:
        if name not in self._tools:
            return f"error: unknown tool {name!r}"
        try:
            return self._tools[name].run(args)
        except Exception as exc:  # tools must never crash the loop
            return f"error: {exc}"


def _safe(path: str) -> str:
    """Confine every file access to the repo (least privilege)."""
    full = os.path.abspath(os.path.join(REPO, path))
    if not (full == REPO or full.startswith(REPO + os.sep)):
        raise ValueError("path escapes repo")
    return full


def default_registry() -> Registry:
    r = Registry()
    r.add(Tool("list_dir", "List entries in a repo-relative directory. args: {path}",
               lambda a: "\n".join(sorted(os.listdir(_safe(a.get("path", ".")))))))
    r.add(Tool("read_file", "Read a repo-relative text file (<=4000 chars). args: {path}",
               lambda a: open(_safe(a["path"]), encoding="utf-8").read()[:4000]))
    return r


# ---------------------------------------------------------------- model ------
@dataclass
class ToolCall:
    name: str
    args: dict


@dataclass
class ModelResponse:
    text: str | None = None                       # a final answer, if any
    tool_calls: list[ToolCall] = field(default_factory=list)


class Model(Protocol):
    """Swap the brain without touching the loop."""
    def complete(self, messages: list[dict], tools: list[dict]) -> ModelResponse: ...


class MockModel:
    """A tiny scripted planner — NOT a real LLM. It inspects the transcript and
    picks the next action by simple heuristics, purely to demonstrate the loop:
    list the skills, read the first one, then summarize."""

    def complete(self, messages, tools) -> ModelResponse:
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        listed = any(m.get("name") == "list_dir" for m in tool_msgs)
        read = any(m.get("name") == "read_file" for m in tool_msgs)
        if not listed:
            return ModelResponse(tool_calls=[ToolCall("list_dir", {"path": "skills"})])
        if not read:
            names = [ln for ln in tool_msgs[0]["content"].splitlines() if ln and not ln.startswith("_")]
            target = f"skills/{names[0]}/SKILL.md" if names else "README.md"
            return ModelResponse(tool_calls=[ToolCall("read_file", {"path": target})])
        return ModelResponse(text=_summarize(tool_msgs))


def _summarize(tool_msgs) -> str:
    listing = ", ".join(x for x in tool_msgs[0]["content"].splitlines() if x)
    desc = next((ln for ln in tool_msgs[1]["content"].splitlines()
                 if ln.startswith("description:")), "(无 description)")
    return (f"仓库 skills/ 下的技能：{listing}\n"
            f"第一个技能的说明 → {desc}\n"
            f"[mini-Claude] 上述结论由 list_dir + read_file 两步工具调用得到。")


class OpenAICompatModel:
    """Point mini-Claude at your internal model gateway (OpenAI-compatible).

    Not used by the offline demo. Requires `pip install openai`. Production tool
    protocols also need to thread tool_call_id back into messages — kept minimal
    here on purpose.
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def complete(self, messages, tools) -> ModelResponse:
        oai_tools = [{"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": {"type": "object", "additionalProperties": True}}} for t in tools]
        chat = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "tool"]
        resp = self.client.chat.completions.create(model=self.model, messages=chat, tools=oai_tools)
        msg = resp.choices[0].message
        if msg.tool_calls:
            return ModelResponse(tool_calls=[
                ToolCall(tc.function.name, json.loads(tc.function.arguments or "{}"))
                for tc in msg.tool_calls])
        return ModelResponse(text=msg.content)


# ---------------------------------------------------------------- skill ------
def load_skill(name: str) -> dict:
    """Harness consumes a SkillHub asset: read skills/<name>/SKILL.md."""
    with open(os.path.join(REPO, "skills", name, "SKILL.md"), encoding="utf-8") as fh:
        text = fh.read()
    body = text.split("---", 2)[2].strip() if text.startswith("---") else text
    return {"name": name, "body": body}


# ----------------------------------------------------------- the loop --------
def run_agent(goal: str, model: Model | None = None, registry: Registry | None = None,
              skill: dict | None = None, max_steps: int = 8, verbose: bool = True) -> str:
    model = model or MockModel()
    registry = registry or default_registry()

    system = "你是 mini-Claude，一个最小智能体。可用工具见 tools，完成任务后直接给出最终答复。"
    if skill:
        system += f"\n\n[已加载技能 {skill['name']}]\n{skill['body']}"

    messages = [{"role": "system", "content": system},
                {"role": "user", "content": goal}]

    for _ in range(max_steps):
        resp = model.complete(messages, registry.specs())
        if resp.tool_calls:
            for tc in resp.tool_calls:
                result = registry.run(tc.name, tc.args)
                if verbose:
                    print(f"  → 工具 {tc.name}({tc.args})  ⇒  {result.splitlines()[0][:60]}...")
                messages.append({"role": "tool", "name": tc.name, "content": result})
            continue
        return resp.text or "(空答复)"
    return "(达到最大步数)"


# ----------------------------------------------------------------- demo ------
if __name__ == "__main__":
    print("=== mini-Claude demo (MockModel, 离线) ===\n")
    skill = load_skill("commit-message")          # harness ← SkillHub asset
    print(f"[harness] 已从 SkillHub 加载技能: {skill['name']}")
    goal = "看看仓库里有哪些技能，并读一下第一个技能的说明。"
    print(f"[user]    {goal}\n")
    answer = run_agent(goal, skill=skill)
    print("\n[mini-Claude]\n" + answer)
