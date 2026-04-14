import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from app.models import ErrorResponse, ScrapeRequest, ScrapeResult, ScrapeResponse

from app.scraper import ScraperError, scrape_website, scrape_website_as_markdown
from app.shortener import generate_short_code
from app.cache import get_cached_result, set_cached_result
from app.config import APP_TITLE, APP_VERSION

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
        cached_result = get_cached_result(request.url)
        if cached_result is not None:
            return cached_result
        
        scraped_data = await scrape_website(request.url)
        short_code = generate_short_code(request.url)
        result = ScrapeResult(
            short_code=short_code,
            data=ScrapeResponse(**scraped_data),
        )
        set_cached_result(request.url, result)

        return result
        

    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/scrape/markdown", responses={400: {"model": ErrorResponse}})
async def scrape_markdown(request: ScrapeRequest) -> Response:
    try:
        markdown_content = await scrape_website_as_markdown(request.url)
        short_code = generate_short_code(request.url)

        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{short_code}.md"'
            },
        )

    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
