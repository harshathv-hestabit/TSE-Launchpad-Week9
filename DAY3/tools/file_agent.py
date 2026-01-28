from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.models.ollama import OllamaChatCompletionClient
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
        parallel_tool_calls=False
    )

from autogen_agentchat.tools import AgentTool

file_surfer = FileSurfer(name="FILE_AGENT",model_client=model_client,base_path="./DAY3/code_output")
file_surfer_tool = AgentTool(agent=file_surfer,return_value_as_last_message=True)

async def file_agent(input:str):
    agent = AssistantAgent(name="File_Agent",model_client=model_client,tools=[file_surfer_tool],
                        #    reflect_on_tool_use=True,
                           system_message=("You are a file agent."
                                           "You can retrieve the absolute path of files in the code_output directory using file surfer tool"
                                           "Process the input query and output the location of the files requested by the user"))
    response = await agent.run(task=input)
    return response.messages[-1].content