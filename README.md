# Web Scraper with Caching and URL Shortening

## Overview

This project is a Python backend application that accepts a URL, scrapes key webpage information, generates a short code for the URL, and stores results in a cache for faster repeated access. When `REDIS_URL` is configured and the Redis client is installed, the app uses Redis with a TTL; otherwise it falls back to an in-memory cache.

The system is built with FastAPI and is structured into separate modules for scraping, caching, short-code generation, models, and tests. The application exposes API endpoints that validate input, fetch webpage content, extract structured HTML data for preview, return downloadable markdown exports, and reuse cached results across repeated requests.

## Objective

The objective of this project was to build a small but complete backend system that demonstrates how multiple backend concepts work together in a practical workflow.

The main areas of focus were:

- making HTTP requests safely
- validating and handling URLs
- parsing HTML content with Beautiful Soup
- building API endpoints with FastAPI
- implementing cache-backed preview and markdown reuse
- tracking repeated preview access with cached click counts
- generating deterministic short codes for URLs
- writing tests for the scraper, cache, API, and shortener modules

This project was also intended to strengthen understanding of modular code structure, exception handling, and testing practices in Python.

The project now also includes AI summarisation support for scraped markdown content using the OpenRouter-compatible OpenAI SDK flow.

## What the Project Does

The application accepts a URL through a `POST /scrape` API endpoint for preview and `POST /scrape/markdown` for markdown export.

It then performs the following steps:

1. validates the URL
2. checks whether the URL already exists in the cache
3. if cached, returns the cached result
4. if not cached, fetches the webpage
5. parses the HTML and extracts:
   - title
   - meta description
   - links
   - images
   - headings
6. generates a short code for the URL
7. stores the final result in cache with the original URL and click metadata
8. returns the response as structured JSON

For markdown export, the application:

1. validates the URL
2. checks whether markdown for that URL already exists in cache
3. if cached, returns the cached markdown file
4. if not cached, fetches the webpage and converts it to markdown
5. stores the generated markdown in cache
6. returns the markdown as a downloadable `.md` attachment

## Example Request

```json
POST /scrape
{
  "url": "https://example.com"
}
```

## Example Response

```json
{
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
export OPENROUTER_HTTP_REFERER=https://localhost:8000
```

The project now includes a chunk-aware OpenRouter summariser in `app/summariser.py`, client setup in `app/openrouter_client.py`, and summary request/response models in `app/summary_models.py`. Large markdown payloads are split into token-sized chunks and combined into a final summary.

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

The summariser currently exists at the service layer. If you are still wiring the summary API route, you can test the summarisation logic independently before exposing it through FastAPI.

## Future Improvements

Planned improvements for the next version of this project include:

- converting the scraping and request-handling flow to an asynchronous implementation for better scalability
- expanding the service further as a REST API with additional endpoints and cleaner resource-oriented design
- exposing the AI summarisation flow through a dedicated FastAPI endpoint
- introducing scrape lifecycle states such as `queued`, `crawling`, `summarising`, and `failed` to better support background processing and progress tracking

## Conclusion

This project demonstrates how a backend application can be built by combining independent components into one workflow. The scraper handles webpage extraction, the shortener produces deterministic short codes, the cache avoids repeated work for the same URL, and the API exposes the final functionality in a usable form.

The main conclusion from this project is that even a small application benefits significantly from modular design and testing. Separating concerns made the code easier to understand and maintain, while writing tests for each module helped validate logic early and reduce debugging time.

Overall, this project served as a practical exercise in backend development, covering API design, HTML parsing, caching, testing, and project structure in Python.
