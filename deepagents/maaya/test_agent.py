import asyncio
from agents.maaya import create_maaya_agent
from server.routers.agent import _msg_to_dict
from pathlib import Path

async def main():
    agent = create_maaya_agent(project_path=str(Path(".").absolute()), model_id="anthropic:claude-sonnet-4-6")
    print("Testing agent.astream")
    
    messages = [{"role": "user", "content": "SUPER SECRET KEYWORD"}]
    printed_count = 0
    async for chunk in agent.astream({"messages": messages}, config={"configurable": {"thread_id": "test-123"}}, stream_mode="values"):
        msgs = chunk.get("messages", [])
        for m in msgs[printed_count:]:
            print(f"Type: {type(m).__name__}, repr: {m}")
            print(f"Dict: {_msg_to_dict(m)}")
        printed_count = len(msgs)

if __name__ == "__main__":
    asyncio.run(main())
