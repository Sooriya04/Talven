# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test script for modular Searqon AI Multi-Session Chat with UUIDv7"""

import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from talven.searqon_ai import SearqonAIOrchestrator
from talven.searqon_ai.storage import history_db

async def main():
    print("Initializing Multi-Session Chat Orchestrator...")
    orchestrator = SearqonAIOrchestrator()
    
    # 1. Start a new conversation
    print("\n--- Test 1: New Conversation ---")
    query1 = "What is the capital of France?"
    result1 = await orchestrator.chat(query1)
    conv_id = result1['conversation_id']
    print(f"New Conversation ID (UUIDv7): {conv_id}")
    print(f"Response: {result1['response']}")
    
    # 2. Continue the same conversation
    print("\n--- Test 2: Continue Conversation ---")
    query2 = "And what is its most famous landmark?"
    result2 = await orchestrator.chat(query2, conversation_id=conv_id)
    print(f"Continued in ID: {result2['conversation_id']}")
    print(f"Response: {result2['response']}")
    
    # 3. Verify history
    print("\n--- Test 3: Verify History ---")
    history = orchestrator.get_history(conv_id)
    print(f"Total messages in thread: {len(history)}")
    for msg in history:
        print(f"  [{msg['role'].upper()}]: {msg['content'][:50]}...")
    
    # 4. List sessions
    print("\n--- Test 4: List Sessions ---")
    sessions = orchestrator.list_sessions()
    print(f"Recent Sessions:")
    for s in sessions:
        print(f"  - {s['title']} (ID: {s['id']})")

if __name__ == "__main__":
    if 'OLLAMA_API_URL' not in os.environ:
        os.environ['OLLAMA_API_URL'] = 'http://127.0.0.1:11434/api/generate'
        
    asyncio.run(main())
