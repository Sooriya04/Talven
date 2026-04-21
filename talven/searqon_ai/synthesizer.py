# SPDX-License-Identifier: AGPL-3.0-or-later
"""LLM Synthesizer for Searqon AI Chat System"""

import os
import httpx
from talven import logger

logger = logger.getChild('searqon_ai.synthesizer')

class ContextSynthesizer:
    def __init__(self):
        self.ollama_url = os.environ.get('OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')
        self.model = os.environ.get('OLLAMA_MODEL', 'qwen2.5:0.5b')
        
    async def synthesize(self, query):
        """
        Generate a simple chat response using Ollama.
        """
        prompt = f"User: {query}\n\nAssistant:"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.ollama_url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get('response', 'Failed to generate response.')
                logger.error(f"Ollama failed with status {resp.status_code}: {resp.text}")
                return f"Error: LLM service returned status {resp.status_code}"
        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}")
            return f"Error: {str(e)}"
