# Web Scraper Project Pipeline

This document reflects what the project currently does and shows how the planned OpenAI SDK summarisation step can fit into the existing flow.

## Current Project Behavior

- FastAPI serves the frontend from `/`.
- `POST /scrape` returns structured JSON for preview and uses cache.
- `POST /scrape/markdown` reads cached markdown first, otherwise fetches the page, converts HTML to markdown, stores it in cache, and returns a downloadable `.md` file.
- URL validation only allows non-empty `https://` URLs.
- Fetching is done with `httpx.AsyncClient(...)` and HTML parsing is done with BeautifulSoup.
- Structured scrape results are cached in memory or Redis with a TTL.
- Markdown content is cached in memory or Redis with a TTL using a dedicated `markdown:{url}` cache key.

## Planned AI Summarisation Concept

- After markdown is available, the app can summarise the markdown with the OpenAI SDK.
- The summary step should work with freshly generated markdown from a new scrape.
- The same step should also work with cached markdown if that file was already generated earlier.
- A summary cache can be added so repeated summary requests do not keep calling the OpenAI API for the same markdown content.

## Mermaid Flowchart

```mermaid
flowchart TD
    Browser["Browser UI<br/>index.html + app.js"] --> Root["GET /"]
    Root --> Static["Serve static UI assets"]
    Static --> Action{"User action"}

    Action -->|Preview scrape result| PreviewRoute["POST /scrape"]
    Action -->|Download markdown| MarkdownRoute["POST /scrape/markdown"]
    Action -->|Future: request AI summary| SummaryRoute["Future summary endpoint or integrated summary action"]

    subgraph PreviewPipeline["Current preview pipeline"]
        PreviewRoute --> PreviewValidate["Validate URL<br/>non-empty + HTTPS only"]
        PreviewValidate -->|invalid URL| ClientError["HTTP 400<br/>detail from ScraperError"]
        PreviewValidate --> PreviewCache{"Structured result cache hit?"}
        PreviewCache -->|Yes| PreviewCached["Return cached ScrapeResult"]
        PreviewCache -->|No| PreviewFetch["fetch_webpage()<br/>httpx AsyncClient"]
        PreviewFetch -->|timeout or HTTP error| ClientError
        PreviewFetch --> PreviewHtml{"Response content is HTML?"}
        PreviewHtml -->|No| ClientError
        PreviewHtml --> PreviewParse["parse_html()<br/>BeautifulSoup"]
        PreviewParse --> PreviewExtract["Extract title, meta description,<br/>links, images, headings"]
        PreviewExtract --> PreviewCode["generate_short_code(url)"]
        PreviewCode --> PreviewBuild["Build ScrapeResult<br/>status_code, timestamps, content_length"]
        PreviewBuild --> PreviewStore["Store structured result<br/>in memory cache or Redis TTL"]
        PreviewStore --> PreviewCached
    end

    PreviewCached --> PreviewResponse["JSON response returned to UI"]
    PreviewResponse --> PreviewRender["Frontend renders preview cards,<br/>metrics, and scraped data panels"]

    subgraph MarkdownPipeline["Current markdown export pipeline"]
        MarkdownRoute --> MarkdownValidate["Validate URL"]
        MarkdownValidate -->|invalid URL| ClientError
        MarkdownValidate --> MarkdownCache{"Markdown cache hit?"}
        MarkdownCache -->|Yes| MarkdownCached["Return cached markdown"]
        MarkdownCache -->|No| MarkdownFetch["fetch_webpage()<br/>httpx AsyncClient"]
        MarkdownFetch -->|timeout or HTTP error| ClientError
        MarkdownFetch --> MarkdownHtml{"Response content is HTML?"}
        MarkdownHtml -->|No| ClientError
        MarkdownHtml --> MarkdownConvert["convert_html_to_markdown()<br/>markdownify"]
        MarkdownConvert --> MarkdownStore["Store markdown<br/>in memory cache or Redis TTL"]
        MarkdownStore --> MarkdownCached
        MarkdownCached --> MarkdownCode["generate_short_code(url)"]
        MarkdownCode --> MarkdownResponse["Return text/markdown attachment<br/>filename = short_code.md"]
    end

    MarkdownResponse --> MarkdownDownload["Browser downloads markdown file"]

    subgraph SummaryPipeline["Planned OpenAI summarisation extension"]
        SummaryRoute --> SummarySource{"Markdown available from where?"}
        MarkdownResponse -. fresh markdown .-> SummarySource
        MarkdownCache -. cached markdown .-> SummarySource
        SummarySource --> SummaryReady["Load markdown content"]
        SummaryReady --> SummaryCache{"Summary cache hit?"}
        SummaryCache -->|Yes| SummaryReturn["Return cached summary"]
        SummaryCache -->|No| OpenAI["OpenAI SDK<br/>summarise markdown content"]
        OpenAI -->|network, rate limit, or API failure| SummaryError["Mark summarisation failed<br/>and return fallback/error"]
        OpenAI --> SummaryStore["Store summary cache<br/>by URL or short_code + markdown fingerprint + model"]
        SummaryStore --> SummaryReturn
    end

    SummaryReturn --> SummaryUi["UI/API returns AI summary beside markdown metadata"]
    ClientError --> ErrorUi["Frontend shows failure state<br/>or API returns error JSON"]
    SummaryError --> ErrorUi
```

## Notes For Implementation

- The current UI already follows a preview-first flow: preview JSON first, then download markdown.
- `POST /scrape` and `POST /scrape/markdown` both use the cache layer now.
- Markdown cache entries are stored separately from preview JSON entries.
- A clean future extension is to add summary read/write cache next.
- Call OpenAI only after markdown is loaded from a fresh scrape or cache.
- Return both the markdown metadata and the generated summary.
