import sqlite3
import re
from typing import Any, Dict, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

FORBIDDEN_SQL_PATTERNS = re.compile(
    r"\b(UPDATE|DELETE|DROP|ALTER|TRUNCATE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)
ALLOWED_WRITE_PATTERNS = re.compile(
    r"^\s*INSERT\s+INTO\b",
    re.IGNORECASE,
)

def connect_db(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def list_tables(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(conn: sqlite3.Connection, table_names: List[str]) -> Dict[str, Any]:
    schemas = {}
    for table in table_names:
        cursor = conn.execute(f"PRAGMA table_info({table});")
        schemas[table] = [
            {
                "column": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "primary_key": bool(row[5]),
            }
            for row in cursor.fetchall()
        ]
    return schemas

def validate_sql(sql: str, allow_write: bool) -> Optional[str]:
    sql_clean = sql.strip()
    if FORBIDDEN_SQL_PATTERNS.search(sql_clean):
        return "UPDATE / DELETE / DDL statements are forbidden."
    is_insert = bool(ALLOWED_WRITE_PATTERNS.match(sql_clean))
    is_select = sql_clean.lower().startswith("select")
    if is_insert and not allow_write:
        return "INSERT attempted without explicit write permission."
    if not (is_select or is_insert):
        return "Only SELECT and INSERT are allowed."
    if is_select and "limit" not in sql_clean.lower():
        return "SELECT queries must include LIMIT."
    return None

def execute_sql(conn: sqlite3.Connection, sql: str) -> Dict[str, Any]:
    cursor = conn.execute(sql)
    if cursor.description:
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return {
            "rows": [dict(zip(columns, row)) for row in rows],
            "row_count": len(rows),
        }
    conn.commit()
    return {"rows_affected": cursor.rowcount}

class SQLiteDBTools:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_tables(self, payload: Optional[dict] = None) -> dict:
        """List all tables in the SQLite database.
        
        Args:
            payload: Empty dict, no parameters needed
            
        Returns:
            Dict with 'tables' key containing list of table names
        """
        payload = payload or {}
        conn = connect_db(self.db_path)
        try:
            return {"tables": list_tables(conn)}
        finally:
            conn.close()

    def inspect_schema(self, payload: dict) -> dict:
        """Inspect the schema of one or more tables.
        
        Args:
            payload: Dict with 'tables' key containing list of table names
                Example: {"tables": ["sales", "sales_metadata"]}
                
        Returns:
            Dict with 'schema' key containing schema information for each table
        """
        tables = payload.get("tables")
        if not tables:
            raise ValueError("Missing 'tables' in payload")
        conn = connect_db(self.db_path)
        try:
            return {"schema": get_table_schema(conn, tables)}
        finally:
            conn.close()

    def execute_query(self, payload: dict) -> dict:
        """Execute a SELECT or INSERT SQL query.
        
        Args:
            payload: Dict with the following keys:
                - 'sql' (required): SQL query string. Must be SELECT or INSERT only.
                  SELECT queries MUST include LIMIT clause.
                  Example: "SELECT * FROM sales WHERE company='Y' LIMIT 10;"
                - 'allow_write' (optional, default=False): Boolean. Set to True to allow INSERT queries.
                  Example: {"sql": "INSERT INTO sales ...", "allow_write": True}
                
        Returns:
            For SELECT: Dict with 'rows' (list of dicts) and 'row_count'
            For INSERT: Dict with 'rows_affected'
        """
        sql = payload.get("sql")
        allow_write = payload.get("allow_write", False)
        if not sql:
            raise ValueError("Missing 'sql' in payload")
        validation_error = validate_sql(sql, allow_write)
        if validation_error:
            raise ValueError(validation_error)
        conn = connect_db(self.db_path)
        try:
            return execute_sql(conn, sql)
        finally:
            conn.close()

SQLITE_DB_SYSTEM_MESSAGE = """You are a SQLite database agent with access to three tools:

1. list_tables: Call with empty payload {} to list all available tables
2. inspect_schema: Call with payload {"tables": ["table_name"]} to see table structure
3. execute_query: Call with payload {"sql": "SQL_HERE"} for SELECT queries, 
   or {"sql": "SQL_HERE", "allow_write": true} for INSERT queries

IMPORTANT PARAMETER NAMES:
- For execute_query, the SQL must be in a parameter named 'sql' (not 'query')
- To enable INSERT, always include "allow_write": true
- SELECT queries MUST include LIMIT clause
- Only SELECT and INSERT are allowed

Always:
- Use tools for all DB access
- Inspect schema before querying unknown tables
- Never use UPDATE, DELETE, or DDL statements
- Never explain results, just provide them"""

SQLITE_DB_SYSTEM_MESSAGE1 = '''You are a database assistant. When asked to retrieve data:

1. First call list_tables() to see what's available
2. Call inspect_schema({"tables": ["table_name"]}) to understand structure
3. Call execute_query({"sql": "SELECT ... LIMIT 100"}) to get actual data

Always complete all three steps. Return the query results.
'''

def db_agent(name: str, db_path: str, model_client) -> AssistantAgent:
    tools_impl = SQLiteDBTools(db_path)
    tools = [
        FunctionTool(
            name="list_tables",
            description="List all tables in the SQLite database. Takes empty payload.",
            func=tools_impl.list_tables,
        ),
        FunctionTool(
            name="inspect_schema",
            description="Inspect schema of tables. Payload: {'tables': ['table1', 'table2']}",
            func=tools_impl.inspect_schema,
        ),
        FunctionTool(
            name="execute_query",
            description="Execute SELECT or INSERT SQL query. Payload: {'sql': 'SELECT...', 'allow_write': True/False}",
            func=tools_impl.execute_query,
        ),
    ]
    return AssistantAgent(
        name=name,
        system_message=(SQLITE_DB_SYSTEM_MESSAGE1),
        model_client=model_client,
        max_tool_iterations=10,
        tools=tools,
    )