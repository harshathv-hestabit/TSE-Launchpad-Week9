from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

class WorkerAgent:
    def __init__(self, name, task, model_client):
        self.agent = AssistantAgent(
            name=name,
            system_message=f"You are a worker. Task: {task}",
            model_client=model_client
        )

    async def run(self, query):
        cancellation = CancellationToken()
        response = await self.agent.on_messages(
            [TextMessage(content=query,source="planner")],cancellation
        )
        return {
            "agent": self.agent.name,
            "output": response.chat_message.content
        }