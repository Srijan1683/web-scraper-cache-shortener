# Web Scraper with Job-Based Crawling, Summarization, and URL Shortening

## Overview

This project is a Python backend application that accepts a URL, creates a background scrape job, extracts webpage data, generates markdown, produces an AI summary, and stores the results in a cache for faster repeated access. When `REDIS_URL` is configured and the Redis client is installed, the app uses Redis with a TTL; otherwise it falls back to an in-memory cache.

The system is built with FastAPI and is structured into separate modules for scraping, caching, short-code generation, summarization, models, and tests. The application exposes job-based scrape endpoints, downloadable markdown export, URL shortener endpoints, and a health check.

## Objective

The objective of this project was to build a small but complete backend system that demonstrates how multiple backend concepts work together in a practical workflow.

The main areas of focus were:

- making HTTP requests safely
- validating and handling URLs
- parsing HTML content with Beautiful Soup
- building API endpoints with FastAPI
- implementing cache-backed scrape, markdown, summary, and job reuse
- tracking short-link usage with cached click counts
- generating deterministic short codes for URLs
- orchestrating AI summarisation with the OpenRouter-compatible OpenAI SDK
- writing tests for the scraper, cache, API, and shortener modules

This project was also intended to strengthen understanding of modular code structure, exception handling, and testing practices in Python.

## What the Project Does

The main API now uses a job-based scrape flow.

When a URL is submitted to `POST /scrape`, the application:

1. validates the URL
2. checks whether a completed job already exists for the same URL and summary type
3. if fully cached, returns the completed job immediately
4. if not cached, creates a queued job and processes it in the background
5. fetches the webpage and extracts:
   - title
   - meta description
   - links
   - images
   - headings
6. generates and caches markdown for the page
7. summarises the markdown with the OpenRouter-compatible OpenAI SDK
8. stores the scrape result, markdown, summary, and job record in cache
9. lets clients retrieve status and results through the job endpoints

The project also exposes:

- `POST /scrape/markdown` to download cached or freshly generated markdown
- `POST /shorten` to create a short code for a URL
- `GET /s/{code}` to redirect using a short code
- `GET /shorten/{code}/stats` to inspect short-link stats
- `GET /health` to verify API and Redis connectivity state

## API Endpoints

### Scrape Job Flow

- `POST /scrape`
  - Submit a URL for scraping and summarization
  - Returns `200` if the result is already fully cached
  - Returns `202` if a background job is queued

- `GET /scrape/{job_id}`
  - Fetch job status and any available result data

- `GET /scrape/{job_id}/summary`
  - Fetch only the AI summary
  - Returns `409` while the job is still processing

- `DELETE /scrape/{job_id}`
  - Delete the job and its cached scrape/markdown/summary data

### Markdown Export

- `POST /scrape/markdown`
  - Return cached or freshly generated markdown as a downloadable `.md` file

### URL Shortener

- `POST /shorten`
  - Create a shortened URL record

- `GET /s/{code}`
  - Redirect to the original URL

- `GET /shorten/{code}/stats`
  - Return click statistics for a short code

### Utility

- `GET /health`
  - Return API health and Redis connectivity status

## Example Job Request

```json
POST /scrape
{
  "url": "https://example.com",
  "summary_type": "brief"
}
```

## Example Job Response

```json
{
  "job_id": "8d9f5dbd85d24c0e9a9de4dd22cf57b9",
  "original_url": "https://example.com/",
  "summary_type": "brief",
  "status": "completed",
  "created_at": "2026-04-25T09:00:00Z",
  "completed_at": "2026-04-25T09:00:04Z",
  "short_code": "a9b9f0",
  "result": {
    "short_code": "a9b9f0",
    "original_url": "https://example.com/",
    "clicks": 0,
    "created_at": "2026-04-25T09:00:00Z",
    "data": {
      "url": "https://example.com/",
      "status_code": 200,
      "status": "crawling",
      "created_at": "2026-04-25T09:00:00Z",
      "completed_at": "2026-04-25T09:00:02Z",
      "content_length": 1256,
      "title": "Example Domain",
      "meta_description": "...",
      "links": [],
      "images": [],
      "headings": []
    }
  },
  "summary": {
    "summary": "Example Domain is a simple placeholder page used for illustrative examples. It explains that the domain may be used in documentation and without coordination.",
    "model": "openai/gpt-4o-mini",
    "token_usage": {
      "prompt_tokens": 120,
      "completion_tokens": 32,
      "total_tokens": 152
    }
  }
}
```

## Example Summary Lookup

```json
GET /scrape/8d9f5dbd85d24c0e9a9de4dd22cf57b9/summary
```

## Example Summary Response

```json
{
  "summary": "Example Domain is a simple placeholder page used for illustrative examples. It explains that the domain may be used in documentation and without coordination.",
  "model": "openai/gpt-4o-mini",
  "token_usage": {
    "prompt_tokens": 120,
    "completion_tokens": 32,
    "total_tokens": 152
  }
}
```

## Running the Application

Start the FastAPI server with:

```bash
PYTHONPATH=. python -m uvicorn app.main:app --reload
```

Optional environment:

```bash
export REDIS_URL=redis://localhost:6379/0
export OPENROUTER_API_KEY=your_openrouter_api_key
export OPENROUTER_MODEL=openai/gpt-4o-mini
export OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

The project includes a chunk-aware OpenRouter summariser in `app/summariser.py`, async client setup in `app/openrouter_client.py`, summary request/response models in `app/summary_models.py`, and the job-based scrape flow in `app/main.py`. Large markdown payloads are split into token-sized chunks and combined into a final summary when they exceed the direct summarisation limit.

If you want a shorter command without manually activating the virtual environment, use:

```bash
python3 run.py
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Deployment

Recommended setup:

- deploy the frontend in `ui/` to Netlify
- deploy the FastAPI backend to Render

### Netlify frontend

This repository includes `netlify.toml`, so Netlify can publish the `ui/` folder directly.

Before deploying the frontend, set the backend URL in `ui/config.js`:

```js
window.WEB_SCRAPER_CONFIG = {
  apiBaseUrl: "https://your-render-service.onrender.com",
};
```

### Render backend

This repository includes `render.yaml` for the FastAPI service.

Set the `CORS_ALLOW_ORIGINS` environment variable in Render to your Netlify site URL, for example:

```text
https://your-site.netlify.app
```

## Running the Tests

Run all tests with:

```bash
PYTHONPATH=. pytest tests/ -v
```

If you are using the integrated VS Code terminal, make sure your `.env` values are actually available in that shell before running the app or summarisation tests.

## Current Architecture

- `app/main.py`
  - FastAPI routes, background job orchestration, shortener endpoints, and health endpoint
- `app/scraper.py`
  - URL validation, fetching, HTML parsing, and markdown conversion
- `app/cache.py`
  - Redis or in-memory cache helpers for scrape results, markdown, summaries, jobs, and short URLs
- `app/summariser.py`
  - OpenRouter/OpenAI-based summarization with token counting and chunk-aware fallback
- `app/openrouter_client.py`
  - Shared async OpenRouter client configuration
- `app/shortener.py`
  - Deterministic short-code generation and validation

## Future Improvements

Planned improvements for the next version of this project include:

- refining deletion behavior so one job delete does not necessarily remove shared cached assets for the same URL
- exposing more metadata such as cache hits, chunking usage, and provider timings
- strengthening provider error handling and retry behavior around summary generation
- aligning the frontend and API docs fully with the job-based workflow

## Conclusion

This project demonstrates how a backend application can be built by combining independent components into one workflow. The scraper handles webpage extraction, the summariser turns markdown into AI-generated summaries, the shortener produces deterministic short codes, the cache avoids repeated work for the same URL, and the API exposes the final functionality through a job-based flow.

The main conclusion from this project is that even a small application benefits significantly from modular design and testing. Separating concerns made the code easier to understand and maintain, while writing tests for each module helped validate logic early and reduce debugging time.

Overall, this project served as a practical exercise in backend development, covering API design, background-style job orchestration, HTML parsing, caching, summarization, testing, and project structure in Python.
