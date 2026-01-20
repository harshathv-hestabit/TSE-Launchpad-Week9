'''
Day 1


# import asyncio
# from autogen_core import CancellationToken
# from autogen_agentchat.messages import TextMessage
# from agents import research_agent as ra, summarizer_agent as sa, answer_agent as aa

# async def main():
#     user_query = "What are some services provided by HestaBit Technologies?"
#     cancellation = CancellationToken()
#     print(f"HV18: {user_query}")
    
#     research = await ra.research_agent.on_messages([TextMessage(content=user_query, source="user")], cancellation)
#     output = research.chat_message.content
#     # print(f"Researcher: {output}")
    
#     summary = await sa.sumarizer_agent.on_messages([TextMessage(content=output, source="researcher")], cancellation)
#     output = summary.chat_message.content
#     # print(f'Summarizer: {output}')
    
#     answer = await aa.answer_agent.on_messages([TextMessage(content=output,source="summarizer")],cancellation)
#     final_answer = answer.chat_message.content
#     print(f'AI: {final_answer}')
    
# asyncio.run(main())

'''

'''
Day 2

import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from orchestration.planner import Planner
from agents.answer_agent import answer_agent

async def main():
    model_client = OllamaChatCompletionClient(
        model="llama3:instruct",
        host="127.0.0.1:11434",
        temperature=0.1
    )
    
    planner = Planner(model_client=model_client)
    query = (
        "Explain how retrieval augmented generation (RAG) works, "
        "including ingestion, indexing, and inference."
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