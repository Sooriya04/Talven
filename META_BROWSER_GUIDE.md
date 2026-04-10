# 🚀 Meta-Browser Development Guide

This guide explains how to integrate the Talven and Searqon backend into a mobile application. It covers everything from API interaction to UI/UX best practices.

## 1. Core Architecture
The system uses an **Asynchronous Hybrid Pipeline**. 
*   **Talven**: Provides lightning-fast search results (Top 10 list).
*   **Searqon**: Provides a deep AI "Overview" (Scraping + LLM).

---

## 2. The API Flow (Step-by-Step)

### Step 1: Execute the Search
When the user types a query, send a `GET` request to Talven. We have optimized this to return in **less than 2 seconds**.

**Endpoint**: `GET http://127.0.0.1:8000/search?q=<query>&format=json`

**Key fields to handle in the response:**
*   `results`: An array of search results to display immediately.
*   `summary_job_id`: A unique ID. The backend has **already started** the AI scraping in a background thread using this ID.

### Step 2: Poll for the AI Summary
While the user is looking at the search results, your app should poll the status of the AI job.

**Endpoint**: `GET http://127.0.0.1:8000/api/v1/searqon/summary/<summary_job_id>`

**Logic for the App**:
1.  Check the `status` field.
2.  If `status` is `pending` or `running`: Wait 1-2 seconds and try again.
3.  If `status` is `completed`: Update the UI with the `result` data.

---

## 3. UI/UX Design Strategy

### Top Section: The AI Overview
*   **State 1 (Loading)**: Show a shimmering "AI is thinking..." placeholder at the top of the search page.
*   **State 2 (Loaded)**: Display the AI summary paragraphs.
*   **Rich Content**: Use the `data.full_source_text` field if you want to allow the user to read the full scraped content in a "Reader View."

### Middle Section: Result List
*   **Rendering**: Each result has a `title`, `url`, and `content`.
*   **UI Style**: Use a "Chrome Lite" style—Blue titles, green URLs, and gray snippets.

---

## 4. Interaction: Opening Websites
When a user clicks a result, you have two choices for the **best user experience**:
1.  **Direct Navigation (System Browser)**: Launch a system `Intent` to open the `url` in the user's default browser (usually **Chrome**).
2.  **In-App Tabs**: Use **Chrome Custom Tabs** (Android) or `SFSafariViewController` (iOS) so the user stays inside your app while getting a full browser experience.

---

## 5. Performance Safeguards
*   **Server Speed**: The backend ruthlessly cuts off slow engines at 1.5 seconds to keep the mobile experience snappy.
*   **Battery Saver**: All the heavy browser scraping and AI work happens on the **server**, not the phone. The phone only parses small JSON packets.

---

## 6. Sample JSON Structure for Reference

**Search Payload:**
```json
{
  "query": "lightpanda browser",
  "summary_job_id": "8f3b...",
  "results": [
    {
      "title": "Lightpanda | The headless browser",
      "url": "https://lightpanda.io/",
      "content": "A fast, lightweight browser engine..."
    }
  ]
}
```

**Completed Summary Payload:**
```json
{
  "status": "completed",
  "result": {
    "comprehensive_overview": "Lightpanda is a high-performance...",
    "key_facts": ["Built with Zig", "9x faster than Chrome"],
    "data": {
      "full_source_text": "..." 
    }
  }
}
```

> [!TIP]
> Always render the search results **immediately**. Never wait for the AI Summary to finish before showing the results list.
