import sqlite3
import json
from langgraph.checkpoint.memory import MemorySaver

# We can't easily access the in-memory MemorySaver from the running FastAPI instance,
# but we CAN check the DB and see what tool the orchestrator called.
conn = sqlite3.connect('maaya_tracker.db')
conn.row_factory = sqlite3.Row
msgs = [dict(r) for r in conn.execute('SELECT role, content, metadata_json FROM chat_messages WHERE project_id=4 ORDER BY id ASC')]
for m in msgs[-15:]:
    print(f"[{m['role']}] {m['metadata_json']}")
    print(f"Content: {m['content'][:100]}")
    print("---")
