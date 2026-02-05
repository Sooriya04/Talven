# Talven API Documentation

Talven provides a simple, JSON-based REST API for retrieving search results.

## Base URL

Defaults to `http://localhost:8888` (or your configured host/port).

---

## Endpoints

### 1. Status Check

**Get API service status.**

- **URL**: `/`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "service": "Talven API",
    "version": "X.Y.Z",
    "message": "Pure RESTful API backend. Use /search endpoint."
  }
  ```

### 2. Health Check

**Simple health check for monitors/load balancers.**

- **URL**: `/healthz`
- **Method**: `GET`
- **Response**: `OK` (text/plain)

### 3. Search

**Perform a search query.**

- **URL**: `/search`
- **Method**: `GET` or `POST`
- **Parameters**:

  | Parameter    | Type   | Required | Description                                                  |
  | :----------- | :----- | :------- | :----------------------------------------------------------- |
  | `q`          | string | **Yes**  | The search query (e.g., `q=python api`).                     |
  | `format`     | string | No       | Output format. Defaults to `json`.                           |
  | `categories` | string | No       | Comma-separated list of categories (e.g., `general,images`). |
  | `pageno`     | int    | No       | Page number (default: 1).                                    |
  | `language`   | string | No       | Language code (e.g., `en-US`, `de`).                         |
  | `time_range` | string | No       | Time range (e.g., `day`, `week`, `month`, `year`).           |
  | `safesearch` | int    | No       | 0 (Off), 1 (Moderate), 2 (Strict).                           |

- **Example Request**:

  ```
  GET /search?q=open+source+projects&format=json
  ```

- **Example Response**:
  ```json
  {
    "query": "open source projects",
    "results": [
      {
        "title": "Open Source Initiative",
        "url": "https://opensource.org/",
        "content": "The steward of the Open Source Definition...",
        "engine": "google",
        "score": 1.0
      },
      ...
    ],
    "number_of_results": 10500000,
    "suggestions": ["open source projects for beginners"]
  }
  ```

## Error Handling

Errors are returned as JSON with an `error` field.

- **400 Bad Request**: Missing query or invalid parameters.
  ```json
  { "error": "No query provided" }
  ```
- **500 Internal Server Error**: Unexpected server-side issues.
