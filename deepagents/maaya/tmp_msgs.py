import sqlite3
import json

conn = sqlite3.connect('maaya_tracker.db')
conn.row_factory = sqlite3.Row
msgs = [dict(r) for r in conn.execute('SELECT role, content FROM chat_messages WHERE project_id=4 ORDER BY id ASC')]
with open('tmp_chat.json', 'w', encoding='utf-8') as f:
    json.dump([m for m in msgs[-10:]], f, indent=2)
