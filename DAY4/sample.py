import os
import asyncio
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
from autogen_core.memory import MemoryContent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from memory.session_memory import SessionMemoryStore
from memory_service import MemoryService
from memory.vector_store import VectorStore, HFEmbedding
from autogen_agentchat.conditions import TextMentionTermination
load_dotenv()

key = os.getenv("GROQ_API_KEY")

async def main():
    session_memory = SessionMemoryStore(max_buffer_size=50)
    embedding = HFEmbedding()
    vector_db = VectorStore(
        embedding_fn=embedding,
        dim=embedding.get_dim(),
        persist_path="DAY4/memory/vector_store"
    )

    memory = MemoryService(
        session_memory=session_memory,
        vector_db=vector_db,
        session_id="chat_1"
    )

    model_client = OpenAIChatCompletionClient(
        model="openai/gpt-oss-120b",
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        model_info={
            "family": "oss",
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "context_length": 4096,
        },
    )

    assistant = AssistantAgent(
        name="assistant",
        description="Helpful assistant",
        model_client=model_client,
        memory=[memory],
        tools=[]
    )

    user = UserProxyAgent(name="user",description="Human user")
    team = RoundRobinGroupChat(participants=[user, assistant], termination_condition=TextMentionTermination("bye"),
        max_turns=20)
    task=TextMessage(content="Start the conversation",source="user")
    
    async for event in team.run_stream(task=task):
        if isinstance(event, TextMessage):
            await memory.add(MemoryContent(content=event.content,mime_type="text/plain"))
            await memory.add_conversation_turn(event.source, event.content)
            print(f"{event.source}: {event.content}")
        elif isinstance(event, TaskResult):
            print("Conversation terminated.")
    await memory.close()
    
if __name__ == "__main__":
    asyncio.run(main())

# import sqlite3
# def main ():
#     conn = sqlite3.connect("DAY4/memory/long_term.db", check_same_thread=False)
#     cur = conn.cursor()
#     cur.execute(
#             """
#             SELECT *
#             FROM long_term_memory
#             ORDER BY created_at DESC
#             """,
#     )
#     rows = cur.fetchall()
#     for row in rows:
#         print(row,end="\n")
        
# if __name__ == "__main__":
#     main()