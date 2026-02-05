# Configuration Guide

Talven (based on SearXNG) is highly configurable via the `talven/settings.yml` file.

## General Settings (`general`)

```yaml
general:
  debug: false # Set to true for development
  instance_name: 'Talven' # Name of your instance
  enable_metrics: true # Enable Prometheus metrics
```

## Server Settings (`server`)

```yaml
server:
  port: 8888 # Port to listen on
  bind_address: '127.0.0.1' # Address to bind to (use 0.0.0.0 for public)
  secret_key: 'change_me' # Secret key for sessions/security
```

## Search Settings (`search`)

```yaml
search:
  safe_search: 0 # 0=None, 1=Moderate, 2=Strict
  autocomplete: 'google' # Autocomplete backend (e.g., google, duckduckgo)
  default_lang: 'auto' # Default language
  formats: # Allowed output formats
    - json
```

## Engines (`engines`)

The core power of Talven comes from its engines. You can enable/disable them in the `engines` list.

```yaml
engines:
  - name: google
    engine: google
    shortcut: g
    disabled: true # Set to false to enable

  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
```

### Enabling an Engine

To enable a search engine (e.g., Google or Wikipedia):

1. Find the engine block in `settings.yml`.
2. Set `disabled: false`.
3. Restart the server.

### Adding Custom Plugins

Plugins can be configured in the `plugins` section.

## Environment Variables

You can override many settings using environment variables, for example:

- `TALVEN_PORT=8080`
- `TALVEN_SECRET=mysecret`
