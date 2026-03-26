Create a new Deep Agents skill (SKILL.md) in the current project.

Ask the user for:
1. **Skill name** — must be lowercase, alphanumeric, hyphens only (e.g. `web-research`, `sql-query`). This becomes both the folder name and the `name` in frontmatter — they MUST match.
2. **What the skill does** — a clear description of the capability
3. **When should the agent use it** — trigger conditions (e.g. "when user asks to research a topic")
4. **Skills folder path** — default is `./skills/`, ask if different
5. **Any specific tools this skill uses** — for the `allowed-tools` field (optional)

Then create:
```
<skills-folder>/<skill-name>/
└── SKILL.md
```

**SKILL.md format** (strictly follow this):
```markdown
---
name: <skill-name>              # MUST match directory name exactly
description: <1-3 sentences describing what it does and when to use it. Include keywords that help the agent recognize when this skill applies.>
license: MIT
allowed-tools: <space-separated tool names, if any>
---

# <Skill Title>

## When to Use
- <Condition 1>
- <Condition 2>

## Process
1. <Step 1>
2. <Step 2>
3. <Step 3>

## Output
- <What the skill produces>
- <Where it saves output, if applicable>

## Example
<A concrete example of the skill being invoked>
```

**Rules:**
- The `name` field in frontmatter MUST exactly match the directory name
- `name` must be lowercase alphanumeric with single hyphens only (no spaces, no uppercase, no `--`)
- `description` must be 1-1024 characters and include trigger keywords
- Keep instructions actionable — the agent reads this when it decides to use the skill

After creating the file, tell the user:
1. The full path to the SKILL.md
2. How to register it in their agent: `skills=["./skills/"]` in `create_deep_agent()`
3. What trigger phrase would cause the agent to use this skill
