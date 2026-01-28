from dataclasses import dataclass, field
from typing import List, Dict, Optional
import threading

@dataclass
class Message:
    role: str
    content: str

@dataclass
class SessionMemory:
    session_id: str
    messages: List[Message] = field(default_factory=list)

class SessionMemoryStore:
    def __init__(self, max_buffer_size: int = 50):
        self._store: Dict[str, SessionMemory] = {}
        self._lock = threading.Lock()
        self.max_buffer_size = max_buffer_size

    def create_session(self, session_id: str) -> None:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = SessionMemory(session_id=session_id)

    def close_session(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = SessionMemory(session_id=session_id)

            memory = self._store[session_id]
            memory.messages.append(Message(role=role, content=content))

            if len(memory.messages) > self.max_buffer_size:
                memory.messages = memory.messages[-self.max_buffer_size:]

    def get_all_messages(self, session_id: str) -> List[Message]:
        with self._lock:
            memory = self._store.get(session_id)
            return list(memory.messages) if memory else []

    def get_recent_messages(self, session_id: str, k: int = 10) -> List[Message]:
        with self._lock:
            memory = self._store.get(session_id)
            if not memory:
                return []
            return memory.messages[-k:]

    def retrieve_relevant_context(self, session_id: str, query: str, k: int = 10) -> List[Message]:
        with self._lock:
            memory = self._store.get(session_id)
            if not memory or not memory.messages:
                return []

            messages = memory.messages
            query_lower = query.lower()
            matched_indices = [
                i for i, msg in enumerate(messages)
                if query_lower in msg.content.lower()
            ]

            results = []
            for i in matched_indices:
                if i - 1 >= 0:
                    results.append(messages[i - 1])
                results.append(messages[i])
                if i + 1 < len(messages):
                    results.append(messages[i + 1])

            seen = set()
            deduped = []
            for msg in results:
                if id(msg) not in seen:
                    seen.add(id(msg))
                    deduped.append(msg)

            if not deduped:
                deduped = messages[-k:]

            return deduped[-k:]