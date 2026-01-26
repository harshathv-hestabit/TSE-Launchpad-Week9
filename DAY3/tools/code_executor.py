import os
import logging
import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.code_execution import PythonCodeExecutionTool
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.messages import ToolCallSummaryMessage
from autogen_agentchat.agents import AssistantAgent
import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GROQ_API_KEY")
model_info = {
        "family": "oss",
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": True,
        "context_length": 4096,
    }

model_client = OpenAIChatCompletionClient(
        model="openai/gpt-oss-20b",
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        model_info=model_info,
    )

# logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

async def code_executor(input: str):
    work_dir = "./code_output"
    executor = LocalCommandLineCodeExecutor(work_dir=work_dir,timeout=600)
    tool = PythonCodeExecutionTool(executor)
    
    client = OllamaChatCompletionClient(model="qwen3:4b")
    agent = AssistantAgent(name="coding_assistant",tools=[tool],model_client=model_client,
                           system_message=(
                           "You are a code executor."
                           "When creating a script:"
                           "- The file must contain valid, readable Python SOURCE CODE"
                           "- Do NOT write literal results (numbers, strings) as the entire file"
                           "- The script must perform the computation when executed"
                           "- Prefer print() for output"
                           ))
    
    result = await agent.run(task=input)
    for msg in result.messages:
        if isinstance(msg, ToolCallSummaryMessage):
            # print(msg.content)
            return msg.content