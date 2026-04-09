from fastapi import FastAPI, HTTPException
from app.models import ErrorResponse, ScrapeRequest, ScrapeResult, ScrapeResponse

from app.scraper import ScraperError, scrape_website
from app.shortener import generate_short_code


app = FastAPI()

    
@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Web Scraper is running"}


@app.post("/scrape", response_model=ScrapeResult, responses={400: {"model": ErrorResponse}})
def scrape(request: ScrapeRequest) -> ScrapeResult:
    try:
        scraped_data = scrape_website(request.url)
        short_code = generate_short_code(request.url)

        return ScrapeResult(
            short_code=short_code,
            data=ScrapeResponse(**scraped_data),
        )

    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
