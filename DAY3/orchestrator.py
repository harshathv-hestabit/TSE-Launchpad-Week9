import asyncio
import os
import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from DAY3.tools.file_agent import file_agent
from DAY3.tools.code_executor import code_executor
from DAY3.tools.db_agent import db_agent

load_dotenv()
from autogen_ext.models.openai import OpenAIChatCompletionClient

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

class PlanStep(BaseModel):
    agent: str
    task: str
    input_keys: List[str] = []
    output_key: str

class ExecutionPlan(BaseModel):
    steps: List[PlanStep]

sys_msg = '''
You are an orchestration planner.

Your job is ONLY to describe an execution plan.
You MUST NOT execute tasks, write code, or produce results.

You MUST return ONLY valid JSON that matches this schema exactly:

ExecutionPlan:
{
  "steps": [
    {
      "agent": "file | db | code",
      "task": "string",
      "input_keys": ["string"],
      "output_key": "string"
    }
  ]
}

Code execution steps are stateless. So use only one code agent. dont add dependencies between two consequent code agents.

STRICT RULES (MANDATORY):

1. Each step MUST include ALL of the following fields:
   - agent
   - task
   - input_keys
   - output_key

2. DO NOT include any other fields.
   - No "id"
   - No "params"
   - No "name"
   - No metadata of any kind

3. "task" MUST be a natural-language instruction for the agent.
   - DO NOT include executable code
   - DO NOT include analysis results
   - DO NOT include reasoning or explanations

4. "output_key" MUST:
   - Be a short snake_case string
   - Be unique across all steps
   - Represent where this step’s output will be stored

5. "input_keys" MUST:
   - Be a list of output_key values from earlier steps
   - Be empty if the step has no dependencies

6. Agent responsibilities:
   - file → locate files
   - db   → read data from tables in the database and execute sql queries
   - code → perform Python analysis using prior outputs. 

7. Steps MUST be ordered by dependency.
   - A step may only depend on outputs from earlier steps.

8. Return ONLY raw JSON.
   - No explanations
   - No markdown
   - No surrounding text
'''

orchestrator = AssistantAgent(
    name="ORCHESTRATOR",
    model_client=model_client,
    system_message=(sys_msg),
    output_content_type_format=ExecutionPlan
)

db = db_agent(name="DB_AGENT",model_client=model_client,db_path="./DAY3/sales.db")

async def run_orchestration(user_query: str) -> Dict[str, any]:
    plan_result = await orchestrator.run(task=user_query)
    plan_json = plan_result.messages[-1].content
    print(json.loads(plan_json))
    plan = ExecutionPlan.model_validate(json.loads(plan_json))
    context: Dict[str, any] = {}

    for step in plan.steps:
        step_context = {k: context[k] for k in getattr(step, "input_keys", []) if k in context}

        if step.agent == "file":
            output = await file_agent(step.task)
            print(output)
            context[step.output_key] = output

        elif step.agent == "db":
            enriched_task = step.task
            if step_context:
                enriched_task += f"\n\nContext:\n{json.dumps(step_context, indent=2,default=str)}"

            output = await db.run(task=enriched_task)
            context[step.output_key] = output
            print(output)

        elif step.agent == "code":
            enriched_task = step.task
            if step_context:
                enriched_task += f"\n\nContext:\n{json.dumps(step_context, indent=2,default=str)}"

            output = await code_executor(enriched_task)
            context[step.output_key] = output
            print(output)

        else:
            raise ValueError(f"Unknown agent type: {step.agent}")

    return context

def summarize_results(context: Dict[str, any]) -> str:
    return "\n".join(f"{k}: {v}" for k, v in context.items())