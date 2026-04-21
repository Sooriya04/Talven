# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test script for modular Searqon AI Chat System"""

import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from talven.searqon_ai import SearqonAIOrchestrator
from talven.searqon_ai.storage import history_db

async def main():
    print("Initializing Searqon AI Chat Orchestrator...")
    orchestrator = SearqonAIOrchestrator()
    
    query = "Hello! Can you help me understand how a chat system works?"
    print(f"\nRunning chat for query: '{query}'")
    
    try:
        result = await orchestrator.chat(query)
        print("\nChat Result:")
        print(f"Response: {result['response'][:200]}...")
        
        # Verify SQLite storage
        print("\nVerifying SQLite storage...")
        history = history_db.get_history(limit=1)
        if history and history[0]['query'] == query:
            print("Successfully stored in history.sqlite")
        else:
            print("Failed to find entry in history.sqlite")
            
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    # Mocking environment variables for test if not set
    if 'OLLAMA_API_URL' not in os.environ:
        os.environ['OLLAMA_API_URL'] = 'http://127.0.0.1:11434/api/generate'
        
    asyncio.run(main())
