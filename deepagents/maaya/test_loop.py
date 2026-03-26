import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"  # fake
# Actually, I can't run Anthropic LLMs locally without a key.
# But I can mock the LLM!
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents import create_deep_agent

model = FakeMessagesListChatModel(responses=[
    AIMessage(content="call task", tool_calls=[{"name": "task", "args": {"description": "foo", "subagent_type": "devops"}, "id": "task1"}]),
    AIMessage(content="done")
])

# I need to mock the environment. It is too complicated.

