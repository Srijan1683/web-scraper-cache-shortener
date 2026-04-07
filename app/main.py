from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.scraper import ScraperError, scrape_website


app = FastAPI()


class ScrapeRequest(BaseModel):
    url: str


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Web scraper API is running."}


@app.post("/scrape")
def scrape(request: ScrapeRequest) -> dict:
    try:
        return scrape_website(request.url)
    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
