'''
Day 1

import asyncio
from autogen_core import CancellationToken
from autogen_core import RoutedAgent
from autogen_agentchat.messages import TextMessage
from DAY1.agents import research_agent as ra, summarizer_agent as sa, answer_agent as aa

async def main():
    user_query = str(input("Ask a question: "))
    cancellation = CancellationToken()
    print(f"HV18: {user_query}")
    
    research = await ra.research_agent.on_messages([TextMessage(content=user_query, source="user")], cancellation)
    output = research.chat_message.content
    print(f"Researcher: {output}")
    await ra.research_agent.close()
    
    summary = await sa.sumarizer_agent.on_messages([TextMessage(content=output, source="researcher")], cancellation)
    output = summary.chat_message.content
    print(f'Summarizer: {output}')
    await sa.sumarizer_agent.close()
    
    answer = await aa.answer_agent.on_messages([TextMessage(content=output,source="summarizer")],cancellation)
    final_answer = answer.chat_message.content
    print(f'AI: {final_answer}')
    await aa.answer_agent.close()
    
asyncio.run(main())

'''

'''
Day 2

import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from DAY2.orchestration.planner import Planner
from DAY1.agents.answer_agent import answer_agent
import os
from dotenv import load_dotenv
load_dotenv()

async def main():
    model_client = OllamaChatCompletionClient(model="qwen3:4b",temperature=0.7)
    # key = os.getenv("GROQ_API_KEY")
    # model_info = {
    #     "family": "oss",
    #     "vision": False,
    #     "function_calling": True,
    #     "json_output": True,
    #     "structured_output": True,
    #     "context_length": 4096,
    # }

    # model_client = OpenAIChatCompletionClient(
    #     model="openai/gpt-oss-120b",
    #     api_key=key,
    #     base_url="https://api.groq.com/openai/v1",
    #     model_info=model_info,
    # )
    
    planner = Planner(model_client=model_client)
    query = (
        "How to learn Agentic AI from basics for a beginner"
    )

    final_answer, execution_tree = await planner.run(query)
    cancellation = CancellationToken()
    result = await answer_agent.on_messages(
        [TextMessage(content=final_answer,source="reflector")],
        cancellation
    )
    print("\nFINAL ANSWER\n")
    print(result.chat_message.content)

    print("\nEXECUTION TREE\n")
    for node_id, data in execution_tree.items():
        print(f"Node: {node_id}")
        print(f"  Deps  : {data['deps']}")
        print(f"  Output:\n{data['output']}\n")

if __name__ == "__main__":
    asyncio.run(main())
'''

'''
Day 3
'''

from DAY3.orchestrator import run_orchestration,summarize_results
from DAY1.agents.answer_agent import answer_agent
import asyncio

async def main():
    user_query = "Analyze sales.csv and generate top 5 insights"
    context = await run_orchestration(user_query)
    final_summary = summarize_results(context)
    task = f"You have to reply to user query: {user_query}, based on the context available below: \n{final_summary}"
    result = await answer_agent.run(task=task)
    print("=== Final Agent Outputs ===")
    print(result.messages[-1].content)

if __name__ == "__main__":
    asyncio.run(main())