# Connecting Searqon AI Chat to the Frontend

The Searqon AI Chat system provides a clean, modular way to integrate LLM-powered chat into your application with built-in history management.

## Backend Integration

The primary entry point is the `SearqonAIOrchestrator.chat()` method.

### Example Flask Endpoint

```python
from flask import Flask, request, jsonify
from talven.searqon_ai import SearqonAIOrchestrator
import asyncio

app = Flask(__name__)
orchestrator = SearqonAIOrchestrator()

@app.route('/api/v2/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query')
    
    # Run the async chat pipeline
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(orchestrator.chat(query))
    
    return jsonify(result)

@app.route('/api/v2/history', methods=['GET'])
def get_history():
    from talven.searqon_ai.storage import history_db
    return jsonify(history_db.get_history())
```

## SQLite History Storage

All chat messages and responses are automatically saved to `talven/searqon_ai_history.sqlite`.

### Storage Schema
- **query**: The user's input.
- **intent**: Fixed to "chat" for this mode.
- **results**: Empty list (reserved for future context/sources).
- **summary**: The AI-generated response.
- **timestamp**: Time of interaction.

## Frontend Example (JavaScript)

```javascript
async function sendMessage(text) {
  const response = await fetch('/api/v2/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: text })
  });
  
  const data = await response.json();
  
  // Display the response in the chat window
  appendMessage('assistant', data.response);
}
```
