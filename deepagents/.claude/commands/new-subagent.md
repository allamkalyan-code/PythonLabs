Add a new subagent definition to an existing Deep Agents project.

Ask the user for:
1. **Subagent name** — used as `subagent_type` when calling `task(subagent_type="...")` (e.g. `researcher`, `sql-writer`, `reviewer`)
2. **What the subagent does** — its specialization
3. **When should the main agent delegate to it** — delegation trigger conditions
4. **Model** — default is `anthropic:claude-haiku-4-5-20251001` (cheaper for subtasks), ask if different
5. **Tools it needs** — any custom tools beyond the defaults (e.g. `web_search`, `run_sql`)
6. **Target file** — which `agent.py` to add it to (default: `./agent.py`)

Read the target `agent.py` first to understand the existing structure, then add the subagent.

**Subagent dict format:**
```python
{
    "name": "<subagent-name>",
    "description": "<When to use this subagent. Be specific — the main agent reads this to decide whether to delegate. Include trigger keywords.>",
    "system_prompt": """You are a <role> specializing in <domain>.

## Your Tools
<List the tools available and what they do>

## Your Process
1. <Step 1>
2. <Step 2>
3. <Step 3>

## Output
<What you produce and where you save it>
""",
    "model": "<model-string>",
    "tools": [<tool_objects>],          # Only if custom tools needed
}
```

**Integration into agent.py:**
- Add the subagent dict to the `subagents=[...]` list in `create_deep_agent()`
- If custom tools are needed, define the `@tool` function(s) above `create_agent()`
- If loading subagents from YAML (like `subagents.yaml`), add the entry there instead

**How the main agent uses it:**
```python
# Main agent calls it like this:
task(subagent_type="<subagent-name>", description="Do X and save results to Y")
```

After the change, show:
1. The subagent dict that was added
2. An example of how the main agent would call it via the `task` tool
3. A reminder to add any required API keys to `.env.example` if new tools were added

**Important rules:**
- Sub-agents get their own context window — they don't share the main agent's conversation history
- Always tell sub-agents WHERE to save their output (they write to files, main agent reads them)
- Cheaper/faster models (haiku) are good for focused subtasks; use the main model for complex reasoning
- The `description` is critical — it's what the main agent reads to decide whether to delegate
