# Web Scraper + Cached URL Shortener

## Overview

This project is a learning exercise designed to help you build a small backend system that combines:

* HTTP networking
* Web scraping
* Data extraction
* API design
* **Caching**
* URL shortening

The system should accept a URL, scrape the webpage, cache the results, and generate a shortened URL that can be used to retrieve the cached data later.

The main goal of this project is to understand **how caching works in real systems**.

---

# Learning Objectives

By completing this project you should gain experience with:

* Making **HTTP requests**
* Understanding **HTTP status codes**
* Parsing and extracting data from **HTML**
* Structuring **Python programs**
* Building a small **web API**
* Implementing a **cache**
* Creating a **URL shortener**
* Handling **errors and edge cases**

---

# High-Level System Behavior

The service should work like this:

1. A user sends a URL to the service
2. The system checks if the URL already exists in the **cache**
3. If cached:

   * return the cached result
4. If not cached:

   * scrape the webpage
   * store the result in the cache
   * generate a **short URL**
   * return the scraped data

This ensures that the same website **is not scraped multiple times unnecessarily**.

---

# Example Workflow

### First Request

Request:

```json
POST /scrape
{
  "url": "https://example.com"
}
```

System behavior:

1. URL is not in cache
2. Website is scraped
3. Data is stored
4. Short code is generated

Response:

```json
{
  "original_url": "https://example.com",
  "short_url": "https://yourservice/s/abc123",
  "cached": false,
  "data": {
    "title": "Example Domain",
    "links": [],
    "images": []
  }
}
```

---

### Second Request (Cached)

Request:

```json
POST /scrape
{
  "url": "https://example.com"
}
```

System behavior:

1. URL found in cache
2. Cached data returned
3. No new scraping performed

Response:

```json
{
  "original_url": "https://example.com",
  "short_url": "https://yourservice/s/abc123",
  "cached": true,
  "data": {...}
}
```

---

# Project Phases

You should build this project in **multiple phases**.

---

# Phase 1 — Fetch a Webpage

Create a Python program that:

* Accepts a **URL**
* Sends an HTTP request
* Prints basic response information

Example:

```bash
python scraper.py https://example.com
```

Output:

```
Status Code: 200
Content Length: 1256 bytes
```

Requirements:

* Only allow **HTTPS URLs**
* Handle invalid URLs
* Handle request timeouts

---

# Phase 2 — Scrape Webpage Content

Extract structured data from the webpage.

Extract:

* Page **title**
* **Meta description**
* All **links**
* All **images**
* All **headings**

Example output:

```json
{
  "title": "Example Domain",
  "meta_description": "...",
  "links": [],
  "images": [],
  "headings": []
}
```

Requirements:

* Handle malformed HTML
* Return empty lists if elements are missing
* Program should not crash

---

# Phase 3 — Build a Web API

Convert the scraper into a web service.

### Endpoint

```
POST /scrape
```

Request:

```json
{
  "url": "https://example.com"
}
```

Response:

```json
{
  "title": "...",
  "links": [...],
  "images": [...]
}
```

---

# Phase 4 — Implement Caching

This is the **core learning goal of the project**.

When a URL is scraped:

1. Store the scraped data
2. Map the URL to a **short code**
3. Return the cached data on future requests

Example cache structure:

```
url_cache:
    url -> short_code

result_cache:
    short_code -> scraped_data
```

This prevents scraping the same site multiple times.

---

# Phase 5 — URL Shortener

Generate a short code for every URL.

Example:

```
abc123 -> https://example.com
```

Short URL format:

```
https://yourservice/s/abc123
```

Add an endpoint:

```
GET /s/{shortcode}
```

This endpoint should redirect the user to the original URL.

---

# Recommended Libraries

The following libraries are strongly recommended for this project.

---

## FastAPI

Used to build the web API.

Documentation:
https://fastapi.tiangolo.com/

FastAPI provides:

* Fast API development
* Automatic OpenAPI documentation
* Built-in request validation
* Excellent async support

Example use:

* Define endpoints
* Handle requests
* Return JSON responses

---

## Pydantic

Used for **data validation and request models**.

Documentation:
https://docs.pydantic.dev/

Pydantic allows you to define structured request and response models.

Example use:

* Validate incoming URLs
* Define API request bodies
* Define response schemas

---

## Requests

Used for making HTTP requests to fetch webpages.

Documentation:
https://requests.readthedocs.io/

Example uses:

* Fetch HTML pages
* Handle response codes
* Handle timeouts

---

## BeautifulSoup

Used for parsing HTML and extracting data.

Documentation:
https://www.crummy.com/software/BeautifulSoup/bs4/doc/

Example uses:

* Extract titles
* Extract links
* Parse page structure

---

## Uvicorn

Used to run the FastAPI server.

Documentation:
https://www.uvicorn.org/

Example usage:

```
uvicorn main:app --reload
```

---

# Error Handling

The system must handle:

* Invalid URLs
* Non-HTTPS URLs
* Network timeouts
* Non-HTML responses
* 404 / 500 responses
* Unexpected HTML structures

The service should **never crash on bad input**.

---

# Bonus Challenges

Optional improvements:

### Cache Expiration (TTL)

Cached results expire after a fixed time.

Example:

* cache expires after **1 hour**

---

### URL Normalization

Treat these URLs as the same:

```
https://example.com
https://example.com/
```

---

### Rate Limiting

Prevent excessive scraping.

---

### Logging

Add structured logging for debugging.

---

# Constraints

* Only scrape **public webpages**
* Do not bypass **anti-bot protections**
* Respect reasonable request limits
* The scraper should work for **most public websites**

---

# Deliverables

Your repository should contain:

* Working Python code
* A functional API server
* Scraper implementation
* URL shortener
* Cache implementation
* Documentation explaining how to run the project

---

# Final Goal

Create a service that:

1. Accepts a URL
2. Scrapes webpage data
3. Stores results in a cache
4. Generates a short URL
5. Returns cached results on repeated requests

This project simulates a **small real-world backend service** and introduces concepts used in production systems.
