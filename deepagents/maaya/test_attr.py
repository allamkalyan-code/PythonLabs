from langchain_core.messages import AIMessage
try:
    result = {"messages": [AIMessage(content="", tool_calls=[{"name": "test", "id": "1", "args": {}}])]}
    message_text = result["messages"][-1].text.rstrip() if getattr(result["messages"][-1], "text", None) else ""
    print(f"SUCCESS: message_text='{message_text}'")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
