import sqlite3
from dataclasses import dataclass, field
from typing import List
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import UserMessage
from memory.session_memory import SessionMemoryStore, Message

import re

STOPWORDS = {
        "the", "is", "at", "which", "on", "a", "an", "and",
        "do", "does", "did", "i", "you", "me", "my", "we",
        "where", "what", "who", "why", "how", "to", "of",
        "in", "for", "it", "this", "that"
    }

def normalize_and_tokenize(text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = text.split()
        tokens = [
            t for t in tokens
            if t not in STOPWORDS and len(t) > 2
        ]

        return tokens

@dataclass
class MemoryContext:
    session_messages: List[Message] = field(default_factory=list)
    vector_memories: List[str] = field(default_factory=list)
    long_term_memories: List[str] = field(default_factory=list)

    def flatten(self) -> List[str]:
        texts = []
        texts.extend(m.content for m in self.session_messages)
        texts.extend(self.vector_memories)
        texts.extend(self.long_term_memories)
        return texts

class MemoryService(Memory):
    def __init__(self,
        session_memory: SessionMemoryStore,
        vector_db=None,
        session_id: str = "default",
        sqlite_path: str = "DAY4/memory/long_term.db"
    ):
        self.session_memory = session_memory
        self.vector_db = vector_db
        self.session_id = session_id
        self.session_memory.create_session(session_id)
        self._conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self._init_long_term_table()

    async def add(self, memory: MemoryContent):
        text = memory.content.strip()
        self._store_long_term(text)
        self.vector_db.add(text=text)

    async def query(self, query: str) -> List[MemoryContent]:
        ctx = self._recall_internal(query)
        print(ctx)
        return [
            MemoryContent(content=text, mime_type=MemoryMimeType.TEXT)
            for text in ctx.flatten()
        ]

    async def add_conversation_turn(self, role: str, content: str):
        self.store_turn(role, content)
    
    async def update_context(self, model_context: ChatCompletionContext):
        messages = await model_context.get_messages()
        query = messages[-1].content if messages else ""
        memories = await self.query(query)
        if not memories:
            return
        
        memory_block = "\n".join(m.content for m in memories)
        text = f"Relevant memory:\n{memory_block}"
        await model_context.add_message(UserMessage(content=text,source="memory"))

    async def clear(self):
        self.session_memory.close_session(self.session_id)
        self.session_memory.create_session(self.session_id)

    async def close(self):
        self.session_memory.close_session(self.session_id)
        self._conn.close()

    def _recall_internal(self, query: str, k: int = 10) -> MemoryContext:
        ctx = MemoryContext()
        session_ctx = self.session_memory.retrieve_relevant_context(self.session_id, query, k)
        if session_ctx:
            ctx.session_messages = session_ctx
            # return ctx
        
        if self.vector_db:
            vector_ctx = self.vector_db.search(query=query, k=k)
            if vector_ctx:
                ctx.vector_memories = vector_ctx
                # return ctx
            
        long_ctx = self._query_long_term(query)
        if long_ctx:
            ctx.long_term_memories = long_ctx
            # return ctx
    
        return ctx

    def store_turn(self, role: str, content: str):
        self.session_memory.add_message(self.session_id,role,content)

    def _init_long_term_table(self):
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ltm_key ON long_term_memory(key)")
        self._conn.commit()

    def _store_long_term(self, text: str):
        cur = self._conn.cursor()
        cur.execute("INSERT INTO long_term_memory (key, value) VALUES (?, ?)",(text, text),)
        self._conn.commit()

    # def _query_long_term(self, query: str, limit: int = 5) -> List[str]:
    #     cur = self._conn.cursor()
    #     cur.execute(
    #         """
    #         SELECT value
    #         FROM long_term_memory
    #         WHERE key LIKE ?
    #         ORDER BY created_at DESC
    #         LIMIT ?
    #         """,
    #         (f"%{query}%", limit),
    #     )
    #     rows = cur.fetchall()
    #     return [row[0] for row in rows]

    def _query_long_term(self, query: str, limit: int = 5) -> List[str]:
        tokens = normalize_and_tokenize(query)

        conditions = " + ".join(
            [f"(value LIKE '%{t}%')" for t in tokens]
        )

        sql = f"""
            SELECT value
            FROM (
                SELECT value,
                    ({conditions}) AS score,
                    created_at
                FROM long_term_memory
            )
            WHERE score > 0
            ORDER BY score DESC, created_at DESC
            LIMIT ?
        """

        cur = self._conn.cursor()
        cur.execute(sql, (limit,))
        return [row[0] for row in cur.fetchall()]
