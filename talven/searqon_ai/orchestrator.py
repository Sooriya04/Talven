# SPDX-License-Identifier: AGPL-3.0-or-later
"""Orchestrator for Searqon AI Chat System with Session Management"""

from .synthesizer import ContextSynthesizer
from .storage import history_db
from talven import logger

logger = logger.getChild('searqon_ai.orchestrator')

class SearqonAIOrchestrator:
    def __init__(self):
        self.synthesizer = ContextSynthesizer()
        
    async def chat(self, query, conversation_id=None):
        """
        Execute a chat interaction.
        If conversation_id is None, a new conversation is created.
        """
        # 1. Handle Conversation ID
        if not conversation_id:
            # Use a snippet of the query as the initial title
            title = (query[:30] + '...') if len(query) > 30 else query
            conversation_id = history_db.create_conversation(title=title)
            logger.info(f"Created new conversation: {conversation_id}")
        
        # 2. Add User Message to History
        history_db.add_message(conversation_id, role="user", content=query)
        
        # 3. Get Conversation History for Context (Optional but recommended)
        # For now, we'll just pass the query, but we could pass previous messages here.
        history = history_db.get_messages(conversation_id)
        
        # 4. Generate Response
        # We can pass the full history to the synthesizer for multi-turn chat
        response = await self.synthesizer.synthesize(query)
        logger.info(f"Generated response for conversation {conversation_id}")
        
        # 5. Add Assistant Message to History
        history_db.add_message(conversation_id, role="assistant", content=response)
        
        return {
            "conversation_id": conversation_id,
            "response": response,
            "history": history_db.get_messages(conversation_id),
            "status": "success"
        }

    def get_history(self, conversation_id):
        """Retrieve the full message history for a conversation."""
        return history_db.get_messages(conversation_id)

    def list_sessions(self):
        """List all available chat sessions."""
        return history_db.list_conversations()
