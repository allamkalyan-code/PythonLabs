from typing import Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import asyncio

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def agent_node(state: State):
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="", tool_calls=[{"name": "test_tool", "args": {}, "id": "1"}])]}

def tools_node(state: State):
    from langgraph.errors import NodeInterrupt
    print("Interrupting!")
    raise NodeInterrupt("Please approve")

builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", "tools")
builder.add_edge("tools", END)

try:
    from langgraph.checkpoint.memory import MemorySaver
    graph = builder.compile(checkpointer=MemorySaver())
    res = graph.invoke({"messages": [HumanMessage(content="run")]}, config={"configurable": {"thread_id": "1"}})
    print("Invoke returned:", res)
except Exception as e:
    print("Invoke raised Exception:", type(e), e)

