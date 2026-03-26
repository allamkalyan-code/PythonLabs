from langchain_core.messages import AIMessage
msg = AIMessage(content="hello")
print(hasattr(msg, "text"))
