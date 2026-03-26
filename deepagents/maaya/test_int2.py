from typing import Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import asyncio
from langgraph.types import interrupt

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def agent_node(state: State):
    interrupt("test")
    return {"messages": []}

builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

try:
    graph = builder.compile()
    res = graph.invoke({"messages": [HumanMessage(content="run")]})
    print("Invoke returned:", res)
except Exception as e:
    print("Invoke raised Exception:", type(e), e)
