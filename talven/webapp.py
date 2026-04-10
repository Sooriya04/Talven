#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""WebApp - Pure API Version"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    
    # Force JSON format if not specified (though pre_request handles default)
    # We ignore csv/rss for now to keep it "pure application/json" unless user specifically requested otherwise and we want to support it. 
    # For now, let's strictly enforce JSON or generic error.
    
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

from talven.webutils import summary_jobs, run_summary_daemon
import uuid

@app.route('/api/v1/searqon/summary', methods=['POST'])
def summary():
    """Independent daemon endpoint to kick off a structured summary job."""
    try:
        data = request.json
        if not data or 'query' not in data:
            return Response(json.dumps({'error': 'query is required'}), status=400, mimetype='application/json')
            
        sq_query = data.get('query')
        talven_urls = data.get('urls', [])
        
        job_id = str(uuid.uuid4())
        summary_jobs[job_id] = {
            'id': job_id,
            'status': 'pending',
            'query': sq_query,
            'result': None,
            'error': None
        }
        
        terminal_log("summary", f"New request for: {sq_query} (Job: {job_id})", color="\033[95m")
        import threading
        thread = threading.Thread(target=run_summary_daemon, args=(job_id, sq_query, talven_urls), daemon=True)
        thread.start()

        return Response(json.dumps({'success': True, 'job_id': job_id, 'status': 'pending'}), status=202, mimetype='application/json')
    except Exception as e:
        logger.exception(e)
        return Response(json.dumps({'error': 'Internal server error'}), status=500, mimetype='application/json')


@app.route('/api/v1/searqon/summary/<job_id>', methods=['GET'])
def get_summary_status(job_id):
    """Polling endpoint to fetch the status/results of a summary job."""
    job = summary_jobs.get(job_id)
    if not job:
        return Response(json.dumps({'error': 'Job not found'}), status=404, mimetype='application/json')
        
    # Strictly return the format requested by the mobile app: {status, result}
    response_data = {
        'status': job.get('status', 'pending'),
        'result': job.get('result')
    }
    
    if job.get('error'):
        response_data['error'] = job['error']
        
    return Response(json.dumps(response_data), mimetype='application/json')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port, debug=False)
