from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from autogen_ext.models.llama_cpp import LlamaCppChatCompletionClient

client=LlamaCppChatCompletionClient(
    model_path="models/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
    n_ctx=8192,
    max_tokens=64,
    temperature=0.7,
    verbose=False
)

answer_agent = AssistantAgent(
    name="Answer_Agent",
    description="used to generate answers to the end user based on the given summarized context",
    system_message=(
        "You are an answer agent"
        "The summarized context is provided to you, for which you will generate the final response to the user."
        "The user has no idea about the summarizer, so dont reveal any implicit info and just take credit for the answer without boasting."
        "If no context was provided, just say that you dont know"
        ),
    model_client=client    
)