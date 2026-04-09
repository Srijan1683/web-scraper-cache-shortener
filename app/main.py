from fastapi import FastAPI, HTTPException
from app.models import ErrorResponse, ScrapeRequest, ScrapeResponse

from app.scraper import ScraperError, scrape_website


app = FastAPI()

    
@app.get("/")
def read_root() -> dict[str, str]:
    return{"message": "Web Scraper is running"}

@app.post("/scrape", response_model=ScrapeResponse, responses={400: {"model": ErrorResponse}})
def scrape(request: ScrapeRequest) -> ScrapeResponse:
    try:
        return ScrapeResponse(**scrape_website(request.url))
    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    