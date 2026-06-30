# 把你们的内部 skill 模板翻译成 schema(自助,无需外泄)

你们的模板目前是"人看的文档约定"。要让 `tools/lint.py` 能自动把关,只需把其中
**结构性规则**抄成 `schema/skill.schema.json`。**这份文件留在你们内网,谁都不用看到内容**
—— linter 引擎对字段一无所知,只照着这份 schema 执行。

元数据在 `SKILL.md` 的 frontmatter,每个 frontmatter 字段 = schema 里 `properties` 的一项。

## 转换速查表(文档措辞 → schema 片段)

| 你文档里大概这么写 | 对应 schema 规则 |
| --- | --- |
| "必须有 X" | 把 `X` 加进 `required` 数组 |
| "X 不能为空" | `"minLength": 1` |
| "X 最多 N 个字" | `"maxLength": N` |
| "X 只能是 A / B / C 之一" | `"enum": ["A","B","C"]` |
| "X 形如 1.2.3" | `"pattern": "^\\d+\\.\\d+\\.\\d+$"` |
| "X 用小写连字符(kebab)" | `"pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"` |
| "X 是一串标签" | `"type": "array", "items": {"type": "string"}` |
| "至少要有一个标签" | 在该数组上加 `"minItems": 1` |

## 一个完整的翻译示例

假设你们文档里有这么几条约定:

> 每个 skill 必须有:名称、用途说明(不少于 20 字)、负责人、成熟度(草稿/试用/正式)。

对应写进 `schema/skill.schema.json`:

```json
{
  "type": "object",
  "required": ["name", "purpose", "owner", "maturity"],
  "properties": {
    "name":     { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$", "maxLength": 64 },
    "purpose":  { "type": "string", "minLength": 20, "maxLength": 1024 },
    "owner":    { "type": "string", "minLength": 1 },
    "maturity": { "type": "string", "enum": ["draft", "trial", "stable"] }
  }
}
```

字段名随你们的真实模板改即可(上面 `purpose`/`maturity` 只是举例)。

## 如果你们的"唯一标识字段"不叫 name

`tools/lint.py` 顶部有一行 `IDENTITY_FIELD = "name"` —— 它是"必须等于目录名且全库唯一"
的那个字段。如果你们的主键叫别的(比如 `id`/`slug`),改这一行即可。

## 边界:schema 只管「结构」,不管「语义」

能写成规则的(必填、格式、枚举、长度)交给 schema 自动拦。但有些约定是**语义**的,机器查不了,
应留给 PR 人工评审(写进 `CONTRIBUTING.md` 的评审清单):

- "description 要说明**何时**该用这个 skill"(措辞质量,机器判断不了)
- "指令要可执行、不含糊"
- "脚本不能有危险副作用"

这正是"**机器把关结构,人只看内容**"——别硬把语义规则塞进 linter。

## 改完怎么验证

1. 把规则填进 `schema/skill.schema.json`。
2. 故意造一个违反某条规则的 skill,`python tools/lint.py` 应当 `FAIL` 并指出那条。
3. 修正后应当 `OK`。无需改任何 Python 代码。
