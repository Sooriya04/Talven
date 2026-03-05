import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
# This automatically handles the stdio communication that nanobot experts.
mcp = FastMCP("SearxNG Custom Search")

# We define a "tool". Nanobot's LLM will automatically see this tool and know how to call it!
@mcp.tool()
async def search(query: str, count: int = 5) -> str:
    """
    Search the web. Use this to find current information, news, or study material.
    """
    
    # ⚠️ REPLACE THIS with the actual URL/Port of your custom SearxNG API
    searxng_api_url = "http://127.0.0.1:8000/search"
    
    # The parameters your reverse-engineered API expects
    params = {
        "q": query,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(searxng_api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
        results = data.get("results", [])[:count]
        if not results:
            return f"No web results found for: {query}"
            
        formatted_results = [f"Results for: {query}\n"]
        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            url = res.get('url', 'No URL')
            content = res.get('content', '')
            
            formatted_results.append(f"{i}. {title}\n   {url}\n   {content}")
            
        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"Error executing web search: {str(e)}"

# Start the server using standard input/output (which nanobot uses to communicate)
if __name__ == "__main__":
    mcp.run(transport='stdio')
