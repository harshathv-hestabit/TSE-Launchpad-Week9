import asyncio
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.llama_cpp import LlamaCppChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient

client = OllamaChatCompletionClient(model="qwen3:0.6b",options={"temperature":0.7})


async def main():        
    # client = LlamaCppChatCompletionClient(
    #     model_path="models/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
    #     temperature=0.2,
    #     n_ctx=2048,
    #     max_tokens=64,
    #     verbose=False,
    # )
    
    shivang = AssistantAgent(
        name="shivang",
        system_message=(
            "You are Shivang"
            "You must tell a UNIQUE joke that Arpit has not told. "
            "You must then explicitly say why Arpit's joke is bad. "
            "Do not repeat jokes. Repetition is a failure."
        ),
        model_client=client,
    )

    arpit = AssistantAgent(
        name="Arpit",
        system_message=(
            "You are Arpit"
            "You must tell a DIFFERENT joke from Shivang. "
            "You must criticize Shivang's joke harshly. "
            "Never repeat or paraphrase the same joke."
        ),
        model_client=client,
    )

    team = RoundRobinGroupChat([shivang, arpit], termination_condition=MaxMessageTermination(3))

    result = await team.run(task="Tell a joke and argue about whose is better.")
    for idx,res in enumerate(result.messages):
        if idx == 0:
            print("Harshath: ",end="")
            print(res.content) 
        elif idx%2 == 1:
            print("Shivang: ",end="")
            print(res.content)
        else:
            print("Arpit: ",end="")
            print(res.content)

asyncio.run(main())