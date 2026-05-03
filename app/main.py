import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.cache import (
    delete_cached_job,
    delete_cached_markdown,
    delete_cached_result,
    delete_cached_summary,
    delete_job_id_for_url,
    get_cached_job,
    get_cached_markdown,
    get_cached_result,
    get_cached_summary,
    get_job_id_for_url,
    get_redis_status,
    get_short_url,
    increment_short_url_clicks,
    set_cached_job,
    set_cached_markdown,
    set_cached_result,
    set_cached_summary,
    set_job_id_for_url,
    set_short_url,
)
from app.config import APP_TITLE, APP_VERSION
from app.models import (
    ErrorResponse,
    HealthResponse,
    ScrapeJobResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeResult,
    ShortenRequest,
    ShortenResponse,
    ShortUrlStats,
    SummaryType,
)
from app.scraper import ScraperError, scrape_website, scrape_website_as_markdown
from app.shortener import generate_short_code
from app.summariser import summarise_markdown
from app.summary_models import SummarizationRequest, SummarizationResult

app = FastAPI(title=APP_TITLE, version=APP_VERSION)
UI_DIR = Path(__file__).resolve().parent.parent / "ui"
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


def _save_job(job: ScrapeJobResponse) -> ScrapeJobResponse:
    set_cached_job(job.job_id, job)
    set_job_id_for_url(str(job.original_url), job.summary_type, job.job_id)
    return job


def _get_job_or_404(job_id: str) -> ScrapeJobResponse:
    job = get_cached_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return job


def _build_scrape_result(url: str, scraped_data: dict) -> ScrapeResult:
    scraped_response = ScrapeResponse(**scraped_data)
    return ScrapeResult(
        short_code=generate_short_code(url),
        original_url=url,
        clicks=0,
        created_at=scraped_response.created_at,
        data=scraped_response,
    )


def _build_completed_job(
    job_id: str,
    url: str,
    summary_type: SummaryType,
    result: ScrapeResult,
    summary: SummarizationResult,
) -> ScrapeJobResponse:
    return ScrapeJobResponse(
        job_id=job_id,
        original_url=url,
        summary_type=summary_type,
        status="completed",
        created_at=result.created_at,
        completed_at=result.data.completed_at or datetime.now(timezone.utc),
        short_code=result.short_code,
        result=result,
        summary=summary,
    )


async def _ensure_markdown(url: str) -> str:
    markdown_content = get_cached_markdown(url)
    if markdown_content is None:
        markdown_content = await scrape_website_as_markdown(url)
        set_cached_markdown(url, markdown_content)
    return markdown_content


async def _ensure_summary(url: str, summary_type: SummaryType) -> SummarizationResult:
    cached_summary = get_cached_summary(url, summary_type)
    if cached_summary is not None:
        return cached_summary

    markdown_content = await _ensure_markdown(url)
    summary_result = await summarise_markdown(markdown_content, summary_type)
    set_cached_summary(url, summary_type, summary_result)
    return summary_result


async def process_scrape_job(job_id: str, url: str, summary_type: SummaryType) -> None:
    job = get_cached_job(job_id)
    if job is None:
        return

    try:
        cached_result = get_cached_result(url)
        if cached_result is None:
            job = _save_job(job.model_copy(update={"status": "crawling", "error": None}))
            scraped_data = await scrape_website(url)
            cached_result = _build_scrape_result(url, scraped_data)
            set_cached_result(url, cached_result)

        job = _save_job(
            job.model_copy(
                update={
                    "status": "summarising",
                    "short_code": cached_result.short_code,
                    "result": cached_result,
                    "error": None,
                }
            )
        )

        cached_summary = await _ensure_summary(url, summary_type)

        _save_job(
            job.model_copy(
                update={
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "summary": cached_summary,
                    "error": None,
                }
            )
        )
    except (ScraperError, ValueError) as exc:
        _save_job(
            job.model_copy(
                update={
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc),
                    "error": str(exc),
                }
            )
        )
    except Exception as exc:
        _save_job(
            job.model_copy(
                update={
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc),
                    "error": f"Unexpected processing error: {exc}",
                }
            )
        )


@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/style.css", include_in_schema=False)
def read_ui_styles() -> FileResponse:
    return FileResponse(UI_DIR / "style.css")


@app.get("/app.js", include_in_schema=False)
def read_ui_script() -> FileResponse:
    return FileResponse(UI_DIR / "app.js")


@app.get("/config.js", include_in_schema=False)
def read_ui_config() -> FileResponse:
    return FileResponse(UI_DIR / "config.js")


@app.post("/scrape", response_model=ScrapeJobResponse, responses={422: {"model": ErrorResponse}})
async def submit_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    url = str(request.url)
    existing_job_id = get_job_id_for_url(url, request.summary_type)
    if existing_job_id is not None:
        existing_job = get_cached_job(existing_job_id)
        if existing_job is not None and existing_job.status != "failed":
            status_code = 200 if existing_job.status == "completed" else 202
            return JSONResponse(status_code=status_code, content=existing_job.model_dump(mode="json"))

    cached_result = get_cached_result(url)
    cached_summary = get_cached_summary(url, request.summary_type)
    if cached_result is not None and cached_summary is not None:
        completed_job = _build_completed_job(
            existing_job_id or uuid4().hex,
            url,
            request.summary_type,
            cached_result,
            cached_summary,
        )
        _save_job(completed_job)
        return JSONResponse(status_code=200, content=completed_job.model_dump(mode="json"))

    queued_job = ScrapeJobResponse(
        job_id=uuid4().hex,
        original_url=request.url,
        summary_type=request.summary_type,
        status="queued",
        created_at=datetime.now(timezone.utc),
        short_code=generate_short_code(url),
    )
    _save_job(queued_job)
    background_tasks.add_task(process_scrape_job, queued_job.job_id, url, request.summary_type)
    return JSONResponse(status_code=202, content=queued_job.model_dump(mode="json"))


@app.get("/scrape/{job_id}", response_model=ScrapeJobResponse, responses={404: {"model": ErrorResponse}})
async def get_scrape_job(job_id: str) -> ScrapeJobResponse:
    return _get_job_or_404(job_id)


@app.get(
    "/scrape/{job_id}/summary",
    response_model=SummarizationResult,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def get_scrape_summary(job_id: str) -> SummarizationResult:
    job = _get_job_or_404(job_id)
    if job.summary is not None:
        return job.summary
    if job.status == "failed":
        raise HTTPException(status_code=409, detail=job.error or "Job failed before summary was created")
    raise HTTPException(status_code=409, detail="Job still processing")


@app.delete("/scrape/{job_id}", status_code=204, responses={404: {"model": ErrorResponse}})
async def delete_scrape_job(job_id: str) -> Response:
    job = _get_job_or_404(job_id)
    url = str(job.original_url)

    delete_cached_job(job_id)
    delete_job_id_for_url(url, job.summary_type)
    delete_cached_summary(url, job.summary_type)
    delete_cached_markdown(url)
    delete_cached_result(url)

    return Response(status_code=204)


@app.post("/scrape/markdown", responses={400: {"model": ErrorResponse}})
async def scrape_markdown(request: ScrapeRequest) -> Response:
    try:
        url = str(request.url)
        markdown_content = await _ensure_markdown(url)
        short_code = generate_short_code(url)

        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{short_code}.md"'
            },
        )
    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/summarize", response_model=SummarizationResult, responses={400: {"model": ErrorResponse}})
async def summarize(request: SummarizationRequest) -> SummarizationResult:
    try:
        return await _ensure_summary(str(request.url), request.max_length)
    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/shorten", response_model=ShortenResponse, status_code=201)
async def create_short_url(request: ShortenRequest) -> ShortenResponse:
    url = str(request.url)
    code = generate_short_code(url)
    short_url_stats = get_short_url(code)

    if short_url_stats is None:
        short_url_stats = ShortUrlStats(
            code=code,
            original_url=request.url,
            clicks=0,
            created_at=datetime.now(timezone.utc),
        )
        set_short_url(code, short_url_stats)

    return ShortenResponse(
        code=code,
        original_url=short_url_stats.original_url,
        short_url=f"/s/{code}",
        created_at=short_url_stats.created_at,
    )


@app.get("/s/{code}", status_code=307, responses={404: {"model": ErrorResponse}})
async def redirect_short_url(code: str) -> RedirectResponse:
    short_url_stats = increment_short_url_clicks(code)
    if short_url_stats is None:
        raise HTTPException(status_code=404, detail="Short code not found")

    return RedirectResponse(url=str(short_url_stats.original_url), status_code=307)


@app.get("/shorten/{code}/stats", response_model=ShortUrlStats, responses={404: {"model": ErrorResponse}})
async def get_short_url_stats(code: str) -> ShortUrlStats:
    short_url_stats = get_short_url(code)
    if short_url_stats is None:
        raise HTTPException(status_code=404, detail="Short code not found")

    return short_url_stats


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", redis=get_redis_status())
