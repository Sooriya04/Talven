# SPDX-License-Identifier: AGPL-3.0-or-later
"""Searqon Microservice Integration"""

import os
import httpx
import json
from talven import logger

# Initialize logger
logger = logger.getChild('searqon')

# Microservice configuration (initialized from environment with defaults)
SEARQON_BASE_URL = os.environ.get('SEARQON_BASE_URL', 'http://127.0.0.1:3001')
SEARQON_UNIFIED_URL = f"{SEARQON_BASE_URL}{os.environ.get('SEARQON_UNIFIED_PATH', '/api/v1/unified')}"
SEARQON_SCRAPE_URL = f"{SEARQON_BASE_URL}{os.environ.get('SEARQON_SCRAPE_PATH', '/api/v1/scrape')}"

def get_searqon_results(sq_query, talven_urls):
    """Synchronously execute Search & Scrape via Searqon microservices and return combined results."""
    try:
        print(f"\033[93m[BACKEND] [SEARCH & SCRAPE] Starting synchronous job for: {sq_query}...\033[0m")
        
        final_results = []
        
        with httpx.Client(timeout=30.0) as client:
            # 1. Unified Search (Global Intelligence)
            try:
                # Default limit 5 as requested
                u_resp = client.post(SEARQON_UNIFIED_URL, json={"query": sq_query, "limit": 5})
                if u_resp.status_code == 200:
                    final_results.extend(u_resp.json())
            except Exception as e:
                logger.error(f"Searqon: Unified search failed: {e}")

            # 2. Batch Scrape (Talven results)
            if talven_urls:
                try:
                    # Take first 2 as requested
                    s_resp = client.post(SEARQON_SCRAPE_URL, json={"url": talven_urls[:2]})
                    if s_resp.status_code == 200:
                        scrape_data = s_resp.json()
                        # If scrape_data is a list of results, extend final_results
                        if isinstance(scrape_data, list):
                            final_results.extend(scrape_data)
                except Exception as e:
                    logger.error(f"Searqon: Batch scrape failed: {e}")

        # Unique results by URL to prevent duplicates
        seen_urls = set()
        merged_results = []
        for r in final_results:
            url = r.get('url')
            if url and url not in seen_urls:
                merged_results.append({
                    "title": r.get('title', 'No Title'),
                    "url": url,
                    "content": r.get('content', r.get('markdown', '')),
                    "source": r.get('source', 'unknown')
                })
                seen_urls.add(url)

        print(f"\033[92m[BACKEND] [SEARCH & SCRAPE] Completed successfully with {len(merged_results)} results.\033[0m")
        return merged_results
    except Exception as e:
        logger.exception(e)
        print(f"\033[91m[BACKEND] [SEARCH & SCRAPE] Failed: {e}\033[0m")
        return []
