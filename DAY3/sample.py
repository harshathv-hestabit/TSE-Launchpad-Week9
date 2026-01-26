# import asyncio
# import os
# from autogen_agentchat.agents import AssistantAgent
# from autogen_agentchat.teams import RoundRobinGroupChat
# from autogen_agentchat.conditions import MaxMessageTermination
# from autogen_ext.models.llama_cpp import LlamaCppChatCompletionClient

# async def main():        
#     client = LlamaCppChatCompletionClient(
#         model_path="models/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
#         temperature=0.2,
#         n_ctx=2048,
#         max_tokens=64,
#         verbose=False,
#     )
    
#     shivang = AssistantAgent(
#         name="shivang",
#         system_message=(
#             "You are Shivang"
#             "You must tell a UNIQUE joke that Arpit has not told. "
#             "You must then explicitly say why Arpit's joke is bad. "
#             "Do not repeat jokes. Repetition is a failure."
#         ),
#         model_client=client,
#     )

#     arpit = AssistantAgent(
#         name="Arpit",
#         system_message=(
#             "You are Arpit"
#             "You must tell a DIFFERENT joke from Shivang. "
#             "You must criticize Shivang's joke harshly. "
#             "Never repeat or paraphrase the same joke."
#         ),
#         model_client=client,
#     )

#     team = RoundRobinGroupChat([shivang, arpit], termination_condition=MaxMessageTermination(3))

#     result = await team.run(task="Tell a joke and argue about whose is better.")
#     for idx,res in enumerate(result.messages):
#         if idx == 0:
#             print("Harshath: ",end="")
#             print(res.content) 
#         elif idx%2 == 1:
#             print("Shivang: ",end="")
#             print(res.content)
#         else:
#             print("Arpit: ",end="")
#             print(res.content)

# asyncio.run(main())

# import sqlite3
# from pathlib import Path

# DB_PATH = Path("sales.db")


# def create_connection(db_path: Path) -> sqlite3.Connection:
#     return sqlite3.connect(db_path)


# def create_tables(conn: sqlite3.Connection) -> None:
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS sales (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             company TEXT NOT NULL,
#             quarter TEXT NOT NULL,
#             year INTEGER NOT NULL,
#             revenue REAL NOT NULL,
#             region TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#         """
#     )

#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS sales_metadata (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             source TEXT NOT NULL,
#             ingested_by TEXT NOT NULL,
#             ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#         """
#     )

#     conn.commit()


# def seed_data(conn: sqlite3.Connection) -> None:
#     seed_rows = [
#         ("Y", "Q1", 2026, 120000.50, "APAC"),
#         ("Y", "Q1", 2026, 83000.75, "EMEA"),
#         ("X", "Q1", 2026, 95000.00, "NA"),
#     ]

#     conn.executemany(
#         """
#         INSERT INTO sales (company, quarter, year, revenue, region)
#         VALUES (?, ?, ?, ?, ?);
#         """,
#         seed_rows,
#     )

#     conn.execute(
#         """
#         INSERT INTO sales_metadata (source, ingested_by)
#         VALUES ('bootstrap', 'sample.py');
#         """
#     )

#     conn.commit()


# def main():
#     if DB_PATH.exists():
#         print(f"Database already exists at {DB_PATH}")
#         return

#     conn = create_connection(DB_PATH)
#     try:
#         create_tables(conn)
#         seed_data(conn)
#         print(f"SQLite database created successfully at {DB_PATH}")
#     finally:
#         conn.close()


# if __name__ == "__main__":
#     main()

# DB_PATH = "sales.db"

# import asyncio
# from pprint import pprint
# from autogen_core import CancellationToken
# from autogen_ext.models.ollama import OllamaChatCompletionClient
# from tools.db_agent import db_agent
# from autogen_agentchat.messages import TextMessage
# import os
# from autogen_ext.models.openai import OpenAIChatCompletionClient
# from dotenv import load_dotenv
# load_dotenv()

# key = os.getenv("GROQ_API_KEY")
# model_info = {
#         "family": "oss",
#         "vision": False,
#         "function_calling": True,
#         "json_output": True,
#         "structured_output": True,
#         "context_length": 4096,
#     }

# model_client = OpenAIChatCompletionClient(
#         model="openai/gpt-oss-120b",
#         api_key=key,
#         base_url="https://api.groq.com/openai/v1",
#         model_info=model_info,
#     )

# async def run_tests():
#     ct = CancellationToken()
#     client = OllamaChatCompletionClient(model="qwen3:4b")
#     agent = db_agent(
#         name="sqlite_db_agent",
#         db_path=DB_PATH,
#         model_client=model_client
#     )

#     print("\n=== TEST 1: List tables ===")
#     result = await agent.on_messages(
#         [TextMessage(content="List all tables in the database", source="user")],
#         ct
#     )
#     pprint(result)

#     print("\n=== TEST 2: Inspect schema (sales) ===")
#     result = await agent.on_messages(
#         [TextMessage(content="Show me the schema for the sales table", source="user")],
#         ct
#     )
#     pprint(result)

#     print("\n=== TEST 3: SELECT query (READ) ===")
#     result = await agent.on_messages(
#         [TextMessage(
#             content="""
#                 Query the sales table to find the total revenue for company 'Y' in Q1.
#                 SELECT company, quarter, year, SUM(revenue) AS total_revenue
#                 FROM sales
#                 WHERE company = 'Y' AND quarter = 'Q1'
#                 GROUP BY company, quarter, year
#                 LIMIT 10;
#             """,
#             source="user"
#         )],
#         ct
#     )
#     pprint(result)

#     print("\n=== TEST 4: INSERT without permission (should fail) ===")
#     result = await agent.on_messages(
#         [TextMessage(
#             content="""
#                 Insert a new sales record:
#                 INSERT INTO sales (company, quarter, year, revenue, region)
#                 VALUES ('Y', 'Q2', 2026, 142000.00, 'APAC');
#             """,
#             source="user"
#         )],
#         ct
#     )
#     pprint(result)

#     print("\n=== TEST 5: INSERT with permission (should succeed) ===")
#     result = await agent.on_messages(
#         [TextMessage(
#             content="""
#                 With write permission enabled, insert this record:
#                 INSERT INTO sales (company, quarter, year, revenue, region)
#                 VALUES ('Y', 'Q2', 2026, 142000.00, 'APAC');
#             """,
#             source="user"
#         )],
#         ct
#     )
#     pprint(result)

#     print("\n=== TEST 6: SELECT inserted row ===")
#     result = await agent.on_messages(
#         [TextMessage(
#             content="""
#                 Query the sales table for the newly inserted record:
#                 SELECT company, quarter, year, revenue, region
#                 FROM sales
#                 WHERE company = 'Y' AND quarter = 'Q2'
#                 LIMIT 10;
#             """,
#             source="user"
#         )],
#         ct
#     )
#     pprint(result)


# if __name__ == "__main__":
#     asyncio.run(run_tests())