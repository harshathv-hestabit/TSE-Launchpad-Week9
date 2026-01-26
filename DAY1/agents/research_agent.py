from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.llama_cpp import LlamaCppChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient

client = OllamaChatCompletionClient(model="qwen3:0.6b",options={"temperature":0.3})

# client=LlamaCppChatCompletionClient(
#     model_path="models/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
#     n_ctx=8192,
#     max_tokens=128,
#     temperature=0.4,
#     verbose=False
# )

research_agent = AssistantAgent(
    name="Research_Agent",
    description="used to perform research on topics and present results in a structured format",
    system_message=(
        "You are a research agent"
        "Find and analyze related to the topic asked by the user."
        "Present your findings in a structured format"
        "Be factual. Do not present any false findings. If you cant find any relevant information, just say so."
        ),
    model_client=client
)