from fastapi import FastAPI, HTTPException
from app.models import ErrorResponse, ScrapeRequest, ScrapeResult, ScrapeResponse

from app.scraper import ScraperError, scrape_website
from app.shortener import generate_short_code
from app.cache import get_cached_result, set_cached_result
from config import APP_TITLE, APP_VERSION

app = FastAPI(title= APP_TITLE, version= APP_VERSION)

    
@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Web Scraper is running"}


@app.post("/scrape", response_model=ScrapeResult, responses={400: {"model": ErrorResponse}})
def scrape(request: ScrapeRequest) -> ScrapeResult:
    try:
        cached_result = get_cached_result(request.url)
        if cached_result is not None:
            return cached_result
        else:
            scraped_data = scrape_website(request.url)
            short_code = generate_short_code(request.url)
            result = ScrapeResult(
                short_code=short_code,
                data=ScrapeResponse(**scraped_data),
            )
            set_cached_result(request.url, result)

        return result
        

    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
