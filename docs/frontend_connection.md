# Connecting Searqon AI Chat (Multi-Session)

The Searqon AI Chat system supports persistent multi-session conversations using **UUIDv7**.

## Backend Integration

The `SearqonAIOrchestrator.chat()` method now manages conversation state and history automatically.

### Example Flask API

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
    conversation_id = data.get('conversation_id') # Optional
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(orchestrator.chat(query, conversation_id))
    
    return jsonify(result)

@app.route('/api/v2/sessions', methods=['GET'])
def list_sessions():
    return jsonify(orchestrator.list_sessions())

@app.route('/api/v2/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id):
    return jsonify(orchestrator.get_history(conversation_id))
```

## SQLite Multi-Session Storage

The database (`talven/searqon_ai_chat.sqlite`) uses two tables:

1.  **`conversations`**: Stores the session metadata (ID, Title, Created At).
2.  **`messages`**: Stores the actual chat logs linked to a conversation.

### UUIDv7 Benefits
We use **UUIDv7** for all IDs. Unlike standard UUIDs (v4), UUIDv7 is **time-ordered**. This means:
*   Database indexes are highly efficient.
*   New conversations and messages are naturally sorted by creation time.
*   IDs provide built-in timestamp information.

## Frontend Usage

### Starting a New Chat
```javascript
// Leave conversation_id empty to start a new thread
const res = await fetch('/api/v2/chat', {
  method: 'POST',
  body: JSON.stringify({ query: "Hello! Who are you?" })
});
const data = await res.json();
const currentConvId = data.conversation_id; // Save this for the next message!
```

### Continuing a Chat
```javascript
// Pass the conversation_id to keep the context
const res = await fetch('/api/v2/chat', {
  method: 'POST',
  body: JSON.stringify({ 
    query: "Tell me more about that.", 
    conversation_id: currentConvId 
  })
});
```

### Loading Session Sidebar
```javascript
const res = await fetch('/api/v2/sessions');
const sessions = await res.json();
// Render your sidebar with session titles and IDs
```
