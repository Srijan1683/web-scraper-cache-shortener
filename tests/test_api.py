from fastapi.testclient import TestClient

from app.main import app
from app.scraper import ScraperError


client = TestClient(app)


def test_scrape_endpoint_returns_scraped_data(monkeypatch):
    def fake_scrape_website(url):
        return {
            "url": url,
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        }

    def fake_generate_short_code(url):
        return "abc123"

    monkeypatch.setattr("app.main.scrape_website", fake_scrape_website)
    monkeypatch.setattr("app.main.generate_short_code", fake_generate_short_code)

    response = client.post("/scrape", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json() == {
        "short_code": "abc123",
        "data": {
            "url": "https://example.com",
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }


def test_scrape_endpoint_returns_400_for_scraper_error(monkeypatch):
    def fake_scrape_website(url):
        raise ScraperError("Only HTTPS URLs are allowed.")

    monkeypatch.setattr("app.main.scrape_website", fake_scrape_website)

    response = client.post("/scrape", json={"url": "http://example.com"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Only HTTPS URLs are allowed."}
