# Web Scraper with Caching and URL Shortening

## Overview

This project is a Python backend application that accepts a URL, scrapes key webpage information, generates a short code for the URL, and stores the result in an in-memory cache for faster repeated access.

The system is built with FastAPI and is structured into separate modules for scraping, caching, short-code generation, models, and tests. The application exposes an API endpoint that validates input, fetches webpage content, extracts structured HTML data, and returns a response containing both the scraped result and a generated short code.

## Objective

The objective of this project was to build a small but complete backend system that demonstrates how multiple backend concepts work together in a practical workflow.

The main areas of focus were:

- making HTTP requests safely
- validating and handling URLs
- parsing HTML content with Beautiful Soup
- building API endpoints with FastAPI
- implementing an in-memory cache
- generating deterministic short codes for URLs
- writing tests for the scraper, cache, API, and shortener modules

This project was also intended to strengthen understanding of modular code structure, exception handling, and testing practices in Python.

## What the Project Does

The application accepts a URL through a `POST /scrape` API endpoint.

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
7. stores the final result in cache
8. returns the response as structured JSON

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
  "data": {
    "url": "https://example.com",
    "status_code": 200,
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
PYTHONPATH=. uvicorn app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Running the Tests

Run all tests with:

```bash
PYTHONPATH=. pytest tests/ -v
```

## Conclusion

This project demonstrates how a backend application can be built by combining independent components into one workflow. The scraper handles webpage extraction, the shortener produces deterministic short codes, the cache avoids repeated work for the same URL, and the API exposes the final functionality in a usable form.

The main conclusion from this project is that even a small application benefits significantly from modular design and testing. Separating concerns made the code easier to understand and maintain, while writing tests for each module helped validate logic early and reduce debugging time.

Overall, this project served as a practical exercise in backend development, covering API design, HTML parsing, caching, testing, and project structure in Python.
