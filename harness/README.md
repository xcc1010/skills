# mini-Claude — 最小智能体 harness

一个约 180 行、**从零实现**的迷你智能体运行时（harness），用来演示真实 agent CLI
（如 Claude Code）的核心架构：

> 一个循环：**模型**决定调用**工具** → harness **执行**工具并把结果喂回 → 直到模型
> 给出最终答复。

它同时会从本仓库的 **SkillHub 加载一个 Skill** 注入系统提示，让你看到三者协同：

```
Harness(mini_claude.py)  ── 加载 ──▶  Skill (skills/<name>/SKILL.md)   ← SkillHub 资产
      │
      └── 模型 ⇄ 工具  循环 ──▶  最终答复
```

> 说明：这里没有任何 Anthropic 专有代码，是自写的教学 harness。Claude Code 的“智能”
> 来自专有的 Claude 模型；而**harness/循环这一层**是可开源、可自建的——本文件就是证明。

## 运行

```
python harness/mini_claude.py
```

零依赖即可跑（内置 `MockModel` 离线模拟“模型”的决策，仅用于演示循环）。

## 结构映射（对应真实 harness 的组成）

| 本文件里的部件 | 对应真实 agent CLI 的概念 |
| --- | --- |
| `run_agent()` 的循环 | agent loop（模型↔工具的主循环） |
| `Registry` / `Tool` | 工具注册与调用（read/list/exec…） |
| `Model` 协议 + `ModelResponse` | 模型后端抽象（可换任意 LLM） |
| `MockModel` | 离线模拟，无需任何 API |
| `OpenAICompatModel` | 接你们**内部模型网关**（OpenAI 兼容） |
| `load_skill()` | harness 消费 SkillHub 资产 |
| `_safe()` 路径限制 | 最小权限（工具只能访问本仓库） |

## 换成真实模型（接内部网关）

`MockModel` 只是为了离线演示。要接你们的内部模型，用 `OpenAICompatModel`：

```python
from harness.mini_claude import run_agent, load_skill, OpenAICompatModel

model = OpenAICompatModel(base_url="https://your-gateway/v1",
                          api_key="...", model="your-internal-model")
print(run_agent("列出仓库技能并读第一个的说明。",
                model=model, skill=load_skill("commit-message")))
```

> 生产实现还需把工具调用的 `tool_call_id` 正确回填进消息（真实的 OpenAI/Anthropic
> tool 协议要求），这里为教学做了简化。

## 参考：Claude Code 与 harness 是否开源

- **Claude Code CLI**：源码在 GitHub 上可获取（`anthropics/claude-code`），但**模型专有**；
  是否可商用需看仓库 LICENSE。
- **Claude Agent SDK**（官方开源）：`anthropics/claude-agent-sdk-python` /
  `-typescript`，可用同样的 tool-use 循环构建自定义 agent。
- 也有社区复刻（如 `Gitlawb/openclaude`）。

结论：**harness/循环这一层是开源、可自建的**（本目录即示例），真正专有的是模型本身。
