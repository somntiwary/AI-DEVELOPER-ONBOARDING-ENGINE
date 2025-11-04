# ==============================
# memory_manager.py
# Memory Manager for RAG Q&A Agent
# ==============================

from pathlib import Path
import json
from typing import List, Dict
from datetime import datetime

class MemoryManager:
    """
    Manages persistent memory for project-specific Q&A sessions.
    Stores previous queries and answers for context-aware responses.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.memory_file = self.base_path / "docs" / "memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_file.exists():
            self._initialize_memory()

    def _initialize_memory(self):
        """Initialize empty memory file."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump({"conversations": []}, f, indent=4)

    def load_memory(self) -> Dict:
        """Load memory from JSON file."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memory: {e}")
            self._initialize_memory()
            return {"conversations": []}

    def save_memory(self, memory: Dict):
        """Save memory to JSON file."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def add_conversation(self, question: str, answer: str, metadata: Dict = None):
        """Add a new Q&A entry to memory with timestamp and metadata."""
        memory = self.load_memory()
        conversation = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "metadata": metadata or {}
        }
        memory["conversations"].append(conversation)
        self.save_memory(memory)

    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Retrieve the last N conversations for context."""
        memory = self.load_memory()
        return memory["conversations"][-limit:]

    def clear_memory(self):
        """Clear all conversation history."""
        self._initialize_memory()

    def get_conversation_count(self) -> int:
        """Get total number of conversations stored."""
        memory = self.load_memory()
        return len(memory["conversations"])

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by question or answer content."""
        memory = self.load_memory()
        query_lower = query.lower()
        matches = []
        
        for conv in memory["conversations"]:
            if (query_lower in conv["question"].lower() or 
                query_lower in conv["answer"].lower()):
                matches.append(conv)
                if len(matches) >= limit:
                    break
        
        return matches


