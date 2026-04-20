# Meta-Browser Backend: Technical Specification (Talven + Searqon)

This document outlines the high-performance search and AI extraction architecture built for the Talven mobile application.

## 1. Architecture Overview

The system is a "hybrid asynchrous pipeline" designed to eliminate search latency while providing Google-style "AI Overviews."

- **Talven (Core Search)**: Handles the meta-discovery across multiple search engines (Bing, Brave, etc.).
- **Searqon (AI Extraction)**: A secondary engine that scrapes top results and uses an LLM (Ollama) to generate a detailed summary.

---

## 2. API Workflow for Integration

### Step A: Initial Search (Instant)

The mobile app hits the search endpoint. The backend is configured with a **1.5s/2.0s ruthlessness limit** to ensure it never hangs.

**Endpoint**: `GET http://127.0.0.1:8000/search?q=<query>&format=json`

**Response Payload**:

```json
{
  "query": "graphify github",
  "summary_job_id": "a1b2c3d4-e5f6-...",
  "results": [
    {
      "title": "raufer/graphify",
      "url": "https://github.com/raufer/graphify",
      "content": "A library to help parsing unstructured text..."
    }
  ]
}
```

> [!IMPORTANT]
> The `summary_job_id` is automatically generated and the background scraping process starts **immediately** without waiting for the frontend.

### Step B: AI Summary Polling (Background)

While the user reads the search results, the app should poll this endpoint in the background using the `summary_job_id`.

**Endpoint**: `GET http://127.0.0.1:8000/api/v1/searqon/summary/<job_id>`

**Possible Statuses**:

- `pending`: Thread is initializing.
- `running`: Searqon is scraping the pages and the LLM is synthesizing.
- `completed`: The data is ready.
- `failed`: An error occurred.

---

## 3. UI/UX Strategy & Execution

### Result Navigation (Chrome/Default Browser)

Every result contains a `url`. To provide a native feeling, the mobile app should execute the following logic:

- When a result is tapped, the app should send an **Intent / Action** to the operating system to open the URL.
- By default, this will launch the user's **Chrome browser** (or default browser).
- **Goal**: This ensures the user gets a secure, full-featured browsing experience for the source website.

### The "AI Overview" Card

- **Top Sector**: Reserved for the content returned by the `completed` summary job.
- **Expansion**: Use the `data.full_source_text` field to provide a "Reader Mode" (distraction-free view) of the scraped pages if the user prefers to stay in the app.

---

## 4. Performance Locks

The following safeguards are implemented in the configuration:

- **Outgoing Timouts**: Capped at 2.0s in `settings.yml` to prevent lagging engines from stalling the mobile app.
- **JSON Enforcement**: Searqon is locked to `format: json` via the Ollama API to prevent malformed responses and hallucinations.
- **Daemonized Threads**: Extraction runs as a Python `daemon=True` thread so it cannot block standard search requests.
