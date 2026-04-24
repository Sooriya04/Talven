#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""WebApp - Pure API Version"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple .env loader since python-dotenv is not installed
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

import json
from timeit import default_timer
import flask
from flask import Flask, Response, request, redirect
from datetime import datetime
from flask_babel import Babel, gettext
import talven
from talven.extended_types import sxng_request
from talven import logger, settings, get_setting
from talven.botdetection import link_token
from talven.exceptions import TalvenParameterException
from talven.engines import categories, engines
from talven import webutils
from talven.webadapter import get_search_query_from_webapp
from talven.preferences import Preferences, ClientPref
from talven.version import VERSION_STRING
import talven.search
import talven.plugins

# Remove UI-related settings that might cause issues if folders are missing
settings['ui']['static_path'] = ''
settings['ui']['templates_path'] = ''

# Initialize search (loads engines, network, metrics)
talven.search.initialize()

logger = logger.getChild('webapp')

# Flask app - No static or template folders
app = Flask(__name__)
app.secret_key = settings['server']['secret_key']

# Minimal Babel setup for core logic that might depend on it
def get_locale():
    # expanded logic might be needed if we want to support 'Accept-Language' header for search results
    return 'en'

babel = Babel(app, locale_selector=get_locale)

def terminal_log(category, message, color="\033[94m"):
    """Pretty print to terminal."""
    reset = "\033[0m"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write(f"{color}[{timestamp}] [{category.upper()}] {message}{reset}\n")
    sys.stderr.flush()

@app.before_request
def pre_request():
    sxng_request.start_time = default_timer()
    sxng_request.errors = []
    sxng_request.timings = []
    
    # Initialize Preferences
    client_pref = ClientPref.from_http_request(sxng_request)
    preferences = Preferences(['simple'], list(categories.keys()), engines, talven.plugins.STORAGE, client_pref)
    sxng_request.preferences = preferences

    # Parse request
    sxng_request.form = dict(request.form.items())
    for k, v in request.args.items():
        if k not in sxng_request.form:
            sxng_request.form[k] = v

    # Default to JSON format
    if 'format' not in sxng_request.form:
        sxng_request.form['format'] = 'json'

    # User plugins setup
    sxng_request.user_plugins = []
    allowed_plugins = preferences.plugins.get_enabled()
    disabled_plugins = preferences.plugins.get_disabled()
    for plugin in talven.plugins.STORAGE:
        if (plugin.id not in disabled_plugins) or plugin.id in allowed_plugins:
            sxng_request.user_plugins.append(plugin.id)

@app.after_request
def add_default_headers(response: flask.Response):
    for header, value in settings['server']['default_http_headers'].items():
        if header not in response.headers:
            response.headers[header] = value
    return response

@app.route('/', methods=['GET'])
def index():
    """Return API Status"""
    return Response(json.dumps({
        "service": "Talven API",
        "version": VERSION_STRING,
        "message": "Pure RESTful API backend. Use /search endpoint."
    }), mimetype='application/json')

@app.route('/healthz', methods=['GET'])
def health():
    return Response('OK', mimetype='text/plain')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search query and return JSON results."""
    
    if not sxng_request.form.get('q'):
        return Response(json.dumps({'error': 'No query provided'}), status=400, mimetype='application/json')

    search_query = None
    result_container = None
    
    try:
        search_query, _, _, _, _ = get_search_query_from_webapp(
            sxng_request.preferences, sxng_request.form
        )
        terminal_log("search", f"Query: {search_query.query}", color="\033[92m")
        search_obj = talven.search.SearchWithPlugins(search_query, sxng_request, sxng_request.user_plugins)
        result_container = search_obj.search()
        terminal_log("search", f"Found {result_container.number_of_results} results", color="\033[92m")

    except TalvenParameterException as e:
        logger.exception('search error: TalvenParameterException')
        return Response(json.dumps({'error': e.message}), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception(e, exc_info=True)
        return Response(json.dumps({'error': 'Internal server error'}), status=500, mimetype='application/json')

    # Return JSON response
    response_content = webutils.get_json_response(search_query, result_container)
    
    # Store response in SQLite
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search_logs.sqlite')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                query TEXT,
                response JSON
            )
        ''')
        cursor.execute('INSERT INTO search_logs (query, response) VALUES (?, ?)', 
                      (search_query.query, response_content))
        conn.commit()
        conn.close()
    except Exception as db_e:
        logger.error(f"Failed to log to SQLite: {db_e}")

    return Response(response_content, mimetype='application/json')

@app.route('/api/v1/summary/<job_id>', methods=['GET', 'POST'])
@app.route('/api/v1/searqon/summary/<job_id>', methods=['GET', 'POST'])
@app.route('/api/v1/summary/status/<job_id>', methods=['GET', 'POST'])
def summary_status(job_id):
    """Retrieve or update the status and results of a background summary job."""
    
    if request.method == 'POST':
        # External push of summary data
        data = request.json or {}
        if job_id not in talven.webutils.summary_jobs:
            return Response(json.dumps({'error': 'Job ID not found'}), status=404, mimetype='application/json')
        
        talven.webutils.summary_jobs[job_id].update({
            'status': data.get('status', 'completed'),
            'summary': data.get('summary'),
            'result': data.get('result', data.get('sources')),
            'full_source_text': data.get('full_source_text')
        })
        terminal_log("summary", f"Job {job_id} updated via POST (Status: {data.get('status')})", color="\033[95m")
        return Response(json.dumps({'status': 'ok'}), mimetype='application/json')

    # GET method - Polling
    job = talven.webutils.summary_jobs.get(job_id)
    if not job:
        return Response(json.dumps({'error': 'Job not found'}), status=404, mimetype='application/json')
    
    return Response(json.dumps(job), mimetype='application/json')
 
# ─── SEARQON AI CHAT V2 ENDPOINTS ───────────────────────────────────────────
from talven.searqon_ai.orchestrator import SearqonAIOrchestrator
orchestrator = SearqonAIOrchestrator()

@app.route('/api/v2/chat', methods=['POST'])
def chat_v2():
    """Execute AI Chat Synthesis with Session Management."""
    data = request.json or {}
    query = data.get('query')
    conversation_id = data.get('conversation_id')
    
    if not query:
        return Response(json.dumps({'error': 'No query provided'}), status=400, mimetype='application/json')
    
    import asyncio
    # We use a helper to run the async orchestrator in a sync Flask route
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(orchestrator.chat(query, conversation_id))
        return Response(json.dumps(result), mimetype='application/json')
    finally:
        loop.close()

@app.route('/api/v2/sessions', methods=['GET'])
def list_sessions_v2():
    """List all chat sessions."""
    sessions = orchestrator.list_sessions()
    return Response(json.dumps(sessions), mimetype='application/json')

@app.route('/api/v2/history/<conversation_id>', methods=['GET'])
def get_history_v2(conversation_id):
    """Get full message history for a conversation."""
    history = orchestrator.get_history(conversation_id)
    return Response(json.dumps(history), mimetype='application/json')
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port, debug=False)

