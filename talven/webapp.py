#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""WebApp - Pure API Version"""

import json
from timeit import default_timer
import flask
from flask import Flask, Response, request, redirect
from flask_babel import Babel, gettext
import talven
from talven.extended_types import sxng_request
from talven import logger, settings, get_setting
from talven.botdetection import link_token
from talven.exceptions import talvenParameterException
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

logger = logger.getChild('webapp')

# Flask app - No static or template folders
app = Flask(__name__)
app.secret_key = settings['server']['secret_key']

# Minimal Babel setup for core logic that might depend on it
def get_locale():
    # expanded logic might be needed if we want to support 'Accept-Language' header for search results
    return 'en'

babel = Babel(app, locale_selector=get_locale)

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
        search_obj = talven.search.SearchWithPlugins(search_query, sxng_request, sxng_request.user_plugins)
        result_container = search_obj.search()

    except SearxParameterException as e:
        logger.exception('search error: SearxParameterException')
        return Response(json.dumps({'error': e.message}), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception(e, exc_info=True)
        return Response(json.dumps({'error': 'Internal server error'}), status=500, mimetype='application/json')

    # Return JSON response
    response_content = webutils.get_json_response(search_query, result_container)
    return Response(response_content, mimetype='application/json')

if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer
    port = int(os.environ.get('PORT', 8888))
    server = WSGIServer(('0.0.0.0', port), app)
    server.serve_forever()
