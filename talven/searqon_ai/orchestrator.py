# SPDX-License-Identifier: AGPL-3.0-or-later
"""Orchestrator for Searqon AI Chat System"""

from .synthesizer import ContextSynthesizer
from .storage import history_db
from talven import logger

logger = logger.getChild('searqon_ai.orchestrator')

class SearqonAIOrchestrator:
    def __init__(self):
        self.synthesizer = ContextSynthesizer()
        
    async def chat(self, query):
        """
        Execute a simple chat and store in history.
        """
        logger.info(f"Starting chat for query: {query}")
        
        # Synthesis (Chat generation)
        response = await self.synthesizer.synthesize(query)
        logger.info("Chat response generated")
        
        # Store in SQLite
        history_db.add_entry(query, intent="chat", results=[], summary=response)
        
        return {
            "query": query,
            "response": response,
            "status": "success"
        }
