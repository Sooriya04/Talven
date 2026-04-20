# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simple Searqon Integration"""

import os
import httpx
import json
from talven import logger

# Initialize logger
logger = logger.getChild('searqon')

# Microservice configuration
SEARQON_BASE_URL = os.environ.get('SEARQON_BASE_URL', 'http://127.0.0.1:3001')
SEARQON_UNIFIED_URL = f"{SEARQON_BASE_URL}{os.environ.get('SEARQON_UNIFIED_PATH', '/api/v1/unified')}"
SEARQON_SCRAPE_URL = f"{SEARQON_BASE_URL}{os.environ.get('SEARQON_SCRAPE_PATH', '/api/v1/scrape')}"

# Ollama configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:0.5b')

def get_ollama_summary(query, text):
    """Fast, simple summary call using 0.5B model."""
    if not text: return "No content available."
    
    prompt = f"Summarize these search results for the query '{query}':\n\n{text[:3000]}\n\nSummary:"
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(OLLAMA_API_URL, json=payload)
            if resp.status_code == 200:
                return resp.json().get('response', 'Failed to generate.')
            return f"Ollama Error: {resp.status_code}"
    except Exception as e:
        return f"Ollama Error: {str(e)}"

def get_searqon_results(sq_query, talven_urls):
    """Simple sequential search, scrape, and summarize."""
    try:
        final_results = []
        
        with httpx.Client(timeout=20.0) as client:
            # 1. Local Scrape (Only Talven Results)
            if talven_urls:
                try:
                    s_resp = client.post(SEARQON_SCRAPE_URL, json={"url": talven_urls[:3]})
                    if s_resp.status_code == 200:
                        final_results.extend(s_resp.json())
                except: pass

        # Dedupe and prepare context
        seen = set()
        merged = []
        for r in final_results:
            url = r.get('url')
            if url and url not in seen:
                merged.append(r)
                seen.add(url)

        full_text = "\n\n".join([f"Source: {r.get('title')}\n{r.get('content', r.get('markdown', ''))}" for r in merged])
        
        # DEBUG PRINTS FOR USER
        print(f"\033[92m[SCRAPE] Successfully gathered {len(merged)} results for summary.\033[0m")
        if merged:
            for i, r in enumerate(merged):
                print(f"  -> [{i+1}] {r.get('title')} ({r.get('url')})")
        
        # 3. Summarize
        ai_summary = get_ollama_summary(sq_query, full_text)
        
        # Format for frontend (url and source only)
        slim_sources = [{"url": r['url'], "source": r.get('source', 'web')} for r in merged]
        
        return {
            "summary": ai_summary,
            "full_source_text": full_text,
            "sources": slim_sources
        }
    except Exception as e:
        return {"summary": f"Process Error: {str(e)}", "full_source_text": "", "sources": []}
