from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage

class ReflectorAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="reflector",
            system_message=(
                "You improve answers by merging multiple responses, "
                "fixing inconsistencies, and increasing clarity."
            ),
            model_client=model_client
        )

    async def run(self, worker_outputs):
        print("Workers have completed jobs")
        cancellation = CancellationToken()
        merged = "\n\n".join(worker_outputs)

        response = await self.agent.on_messages(
            [TextMessage(content=merged,source="workers")],cancellation
        )
        return response.chat_message.content