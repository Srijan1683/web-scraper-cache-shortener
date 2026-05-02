# Web Scraper Project Pipeline

This document reflects the current backend flow of the project after the move to a job-based scrape pipeline.

## Current Project Behavior

- FastAPI serves the frontend from `/`.
- `POST /scrape` creates or reuses a scrape job for a URL and summary type.
- `GET /scrape/{job_id}` returns job status and any available result data.
- `GET /scrape/{job_id}/summary` returns the AI summary when available.
- `DELETE /scrape/{job_id}` removes the job and its cached scrape, markdown, and summary data.
- `POST /scrape/markdown` returns cached or freshly generated markdown as a downloadable file.
- `POST /shorten`, `GET /s/{code}`, and `GET /shorten/{code}/stats` handle the URL-shortener flow.
- `GET /health` reports API health and Redis connectivity state.
- Redis is used when `REDIS_URL` is configured; otherwise the app falls back to in-memory cache with the same TTL behavior.

## Mermaid Flowchart

```mermaid
flowchart TD
    Browser["Browser / Client"] --> Submit["POST /scrape<br/>url + summary_type"]
    Browser --> JobLookup["GET /scrape/{job_id}"]
    Browser --> SummaryLookup["GET /scrape/{job_id}/summary"]
    Browser --> DeleteJob["DELETE /scrape/{job_id}"]
    Browser --> MarkdownRoute["POST /scrape/markdown"]
    Browser --> ShortenRoute["POST /shorten"]
    Browser --> RedirectRoute["GET /s/{code}"]
    Browser --> StatsRoute["GET /shorten/{code}/stats"]
    Browser --> HealthRoute["GET /health"]

    subgraph ScrapeJobPipeline["Scrape job pipeline"]
        Submit --> Validate["Validate URL"]
        Validate -->|invalid| RequestError["422 / 400 error"]
        Validate --> JobCheck{"Existing job or<br/>fully cached assets?"}

        JobCheck -->|Yes| CachedReturn["Return existing/completed job<br/>HTTP 200 or 202"]
        JobCheck -->|No| QueueJob["Create queued job + job_id"]
        QueueJob --> SaveJob["Cache job + job map"]
        SaveJob --> Accepted["Return queued job<br/>HTTP 202"]
        SaveJob --> Background["Background processing"]

        Background --> Crawl["Status: crawling<br/>fetch + parse HTML"]
        Crawl -->|fetch / HTML error| JobFailed["Status: failed<br/>store error"]
        Crawl --> StoreResult["Cache ScrapeResult"]
        StoreResult --> Summarising["Status: summarising"]
        Summarising --> MarkdownCheck{"Markdown cached?"}
        MarkdownCheck -->|No| BuildMarkdown["Fetch page as markdown"]
        MarkdownCheck -->|Yes| ReuseMarkdown["Reuse cached markdown"]
        BuildMarkdown --> StoreMarkdown["Cache markdown:{url}"]
        StoreMarkdown --> SummaryCheck
        ReuseMarkdown --> SummaryCheck{"Summary cached?"}

        SummaryCheck -->|Yes| ReuseSummary["Reuse cached summary"]
        SummaryCheck -->|No| Summarise["OpenRouter summary<br/>direct or chunked"]
        Summarise -->|provider / validation error| JobFailed
        Summarise --> StoreSummary["Cache summary:{summary_type}:{url}"]
        StoreSummary --> CompleteJob["Status: completed<br/>attach result + summary"]
        ReuseSummary --> CompleteJob
        CompleteJob --> SaveFinal["Persist completed job"]
    end

    JobLookup --> JobFetch{"job exists?"}
    JobFetch -->|Yes| JobResponse["Return job status + data"]
    JobFetch -->|No| JobNotFound["404 job not found"]

    SummaryLookup --> SummaryFetch{"job exists and<br/>summary ready?"}
    SummaryFetch -->|Yes| SummaryResponse["Return summary<br/>HTTP 200"]
    SummaryFetch -->|No, still running| SummaryPending["409 still processing"]
    SummaryFetch -->|No, missing job| JobNotFound

    DeleteJob --> DeleteFetch{"job exists?"}
    DeleteFetch -->|Yes| DeleteAssets["Delete job, scrape cache,<br/>markdown cache, summary cache"]
    DeleteFetch -->|No| JobNotFound
    DeleteAssets --> DeleteDone["204 No Content"]

    subgraph UtilityFlows["Utility flows"]
        MarkdownRoute --> MarkdownCheck2{"Markdown cached?"}
        MarkdownCheck2 -->|Yes| MarkdownReturn["Return markdown file"]
        MarkdownCheck2 -->|No| MarkdownBuild["Fetch + convert to markdown"]
        MarkdownBuild --> MarkdownStore2["Cache markdown"]
        MarkdownStore2 --> MarkdownReturn

        ShortenRoute --> ShortenCreate["Generate code + cache short URL"]
        ShortenCreate --> ShortenReturn["Return ShortenResponse"]

        RedirectRoute --> RedirectCheck{"short code exists?"}
        RedirectCheck -->|Yes| RedirectOut["Increment clicks + 307 redirect"]
        RedirectCheck -->|No| ShortError["404 short code not found"]

        StatsRoute --> StatsCheck{"short code exists?"}
        StatsCheck -->|Yes| StatsReturn["Return ShortUrlStats"]
        StatsCheck -->|No| ShortError

        HealthRoute --> HealthReturn["Return status ok + redis connected/disconnected"]
    end
```

## Notes

- The primary user flow is now job-based rather than direct preview JSON.
- The same URL can reuse cached scrape results, markdown, and summaries across repeated requests.
- Summary caching is separated by `summary_type`, so `brief` and `detailed` are stored independently.
- Background processing updates job states through `queued`, `crawling`, `summarising`, `completed`, and `failed`.
- The delete endpoint currently removes both the job record and the cached assets tied to that URL and summary type.
