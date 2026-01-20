from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

class ValidatorAgent:
    def __init__(self, model_client):
        self.agent = AssistantAgent(
            name="validator",
            system_message=(
                "You validate answers. "
                "Check for factual errors, logical mistakes, or missing steps."
            ),
            model_client=model_client
        )

    async def run(self, content):
        cancellation = CancellationToken()
        print("Validator has received input")
        response = await self.agent.on_messages(
            [TextMessage(content=content,source="Reflector")],cancellation
        )
        return response.chat_message.content