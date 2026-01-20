import asyncio
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
from agents import research_agent as ra, summarizer_agent as sa, answer_agent as aa

async def main():
    user_query = "What are some services provided by HestaBit Technologies?"
    cancellation = CancellationToken()
    print(f"HV18: {user_query}")
    
    research = await ra.research_agent.on_messages([TextMessage(content=user_query, source="user")], cancellation)
    output = research.chat_message.content
    # print(f"Researcher: {output}")
    
    summary = await sa.sumarizer_agent.on_messages([TextMessage(content=output, source="researcher")], cancellation)
    output = summary.chat_message.content
    # print(f'Summarizer: {output}')
    
    answer = await aa.answer_agent.on_messages([TextMessage(content=output,source="summarizer")],cancellation)
    final_answer = answer.chat_message.content
    print(f'AI: {final_answer}')
    
asyncio.run(main())