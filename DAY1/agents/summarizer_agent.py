from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.llama_cpp import LlamaCppChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient

client = OllamaChatCompletionClient(model="qwen3:0.6b",options={"temperature":0.5})

# client=LlamaCppChatCompletionClient(
#     model_path="models/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
#     n_ctx=8192,
#     max_tokens=84,
#     temperature=0.6,
#     verbose=False
# )

sumarizer_agent = AssistantAgent(
    name="Summarizer_Agent",
    description="used to summarize research related content in an understandable format to the user.",
    system_message=(
        "You are a summarizer agent"
        "Present the results in a concise format to the user."
        "Present sources if any found in results otherwise don't mention it"
        "If no relevant information was given to you, just say so."
        ),
    model_client=client
)