import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.cache import (
    get_cached_markdown,
    get_cached_result,
    get_cached_summary,
    increment_result_clicks,
    set_cached_markdown,
    set_cached_result,
    set_cached_summary,
)
from app.config import APP_TITLE, APP_VERSION
from app.models import ErrorResponse, ScrapeRequest, ScrapeResult, ScrapeResponse
from app.scraper import ScraperError, scrape_website, scrape_website_as_markdown
from app.shortener import generate_short_code
from app.summariser import summarise_markdown
from app.summary_models import SummarizationRequest, SummarizationResult

app = FastAPI(title= APP_TITLE, version= APP_VERSION)
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


@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/style.css", include_in_schema=False)
def read_ui_styles() -> FileResponse:
    return FileResponse(UI_DIR / "style.css")


@app.get("/app.js", include_in_schema=False)
def read_ui_script() -> FileResponse:
    return FileResponse(UI_DIR / "app.js")


@app.post("/scrape", response_model=ScrapeResult, responses={400: {"model": ErrorResponse}})
async def scrape(request: ScrapeRequest) -> ScrapeResult:
    try:
        url = str(request.url)
        cached_result = get_cached_result(url)
        if cached_result is not None:
            incremented_result = increment_result_clicks(url)
            return incremented_result or cached_result
        
        scraped_data = await scrape_website(url)
        short_code = generate_short_code(url)
        scraped_response = ScrapeResponse(**scraped_data)
         
        result = ScrapeResult(
            short_code=short_code,
            original_url=request.url,
            clicks=0,
            created_at=scraped_response.created_at,
            data=scraped_response,
        )
        set_cached_result(url, result)

        return result
        

    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/scrape/markdown", responses={400: {"model": ErrorResponse}})
async def scrape_markdown(request: ScrapeRequest) -> Response:
    try:
        url = str(request.url)
        markdown_content = get_cached_markdown(url)
        if markdown_content is None:
            markdown_content = await scrape_website_as_markdown(url)
            set_cached_markdown(url, markdown_content)

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
        cached_summary = get_cached_summary(request.content, request.max_length)
        if cached_summary is not None:
            return cached_summary

        summary_result = await summarise_markdown(request.content, request.max_length)
        set_cached_summary(request.content, request.max_length, summary_result)
        return summary_result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
