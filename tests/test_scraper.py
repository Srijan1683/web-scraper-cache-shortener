import pytest
from app.scraper import ScraperError, parse_html, validate_url, scrape_website

def test_validate_url_returns_cleaned_https_url():
    url = "https://example.com"
    
    result = validate_url(url)
    
    assert result == "https://example.com"
    
def test_validate_url_raises_error_for_empty_url():
    url = ""
    
    with pytest.raises(ScraperError, match= "The URL cannot be empty"):
        validate_url(url)
   
        
def test_validate_url_raises_error_for_non_https_url():
    url = "file://example.com"
    
    with pytest.raises(ScraperError, match= "Only HTTPS URLs are allowed"):
        validate_url(url)
        
    
def test_validate_url_raises_error_for_missing_domain():
    url = "https://"
    
    with pytest.raises(ScraperError, match= "Invalid URL Domain request"):
        validate_url(url)
        
"""def parse_html(html:str) -> dict[str,Any]:
    
    soup = BeautifulSoup(html,"html.parser")
    
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    
    return {
        "title": title,
        "meta_description": _extract_meta_description(soup),
        "links": _extract_links(soup),
        "images": _extract_images(soup),
        "headings": _extract_headings(soup),
    }"""


def test_parse_html_extracts_title_meta_links_images_and_headings():
    html = """
    <html>
        <head>
            <title>Example Domain</title>
            <meta name="description" content="Example description">
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Sub Heading</h2>
            <a href="https://example.com/page">Example Link</a>
            <img src="https://example.com/image.jpg">
        </body>
    </html>
    """

    result = parse_html(html)

    assert result["title"] == "Example Domain"
    assert result["meta_description"] == "Example description"
    assert result["links"] == ["https://example.com/page"]
    assert result["images"] == ["https://example.com/image.jpg"]
    assert result["headings"] == ["Main Heading", "Sub Heading"]
    

def test_parse_html_returns_empty_values_for_missing_elements():
    html = "<html><body><p>No useful tags here</p></body></html>"

    result = parse_html(html)

    assert result["title"] == ""
    assert result["meta_description"] == ""
    assert result["links"] == []
    assert result["images"] == []
    assert result["headings"] == []


"""def scrape_website(url:str, timeout:int = DEFAULT_TIMEOUT) -> dict[str,Any]:
    
    response = fetch_webpage(url,timeout=timeout)
    content_type = response.headers.get("Content-Type","")
    
    if "html" not in content_type.lower():
        raise ScraperError("The URL did not return HTML page")
    
    scraped_data = parse_html(response.text)
    
    scraped_data.update(
        {"url": response.url,
         "status_code": response.status_code,
         "content_length": len(response.content),
        }
    )
    return scraped_data"""

def test_scrape_website_returns_structured_data(monkeypatch):
    class FakeResponse:
        url = "https://example.com"
        status_code = 200
        text = """
        <html>
            <head>
                <title>Example Domain</title>
                <meta name="description" content="Example Description"
            </head>
            <body>
                <h1>Main Heading</h1>
                <a href="https://example.com/page">Example Link</a>
                <img src="https://example.com/image.jpg">
            </body>
        </html>
        """
        content = text.encode()
        headers = {"Content-Type": "text/html; charset=utf-8"}

    async def fake_fetch_webpage(url, timeout=10):
        return FakeResponse()

    monkeypatch.setattr("app.scraper.fetch_webpage", fake_fetch_webpage)

    result = scrape_website("https://example.com")

    assert result["url"] == "https://example.com"
    assert result["status_code"] == 200
    assert result["content_length"] == len(FakeResponse.content)
    assert result["title"] == "Example Domain"
    assert result["meta_description"] == "Example Description"
    assert result["links"] == ["https://example.com/page"]
    assert result["images"] == ["https://example.com/image.jpg"]
    assert result["headings"] == ["Main Heading"]
    

def test_scrape_website_raises_error_for_non_html_response(monkeypatch):
    class FakeResponse:
        url = "https://example.com/file.pdf"
        status_code = 200
        text = "Not HTML"
        content = text.encode()
        headers = {"Content-Type": "application/pdf"}

    async def fake_fetch_webpage(url, timeout=10):
        return FakeResponse()

    monkeypatch.setattr("app.scraper.fetch_webpage", fake_fetch_webpage)

    with pytest.raises(ScraperError, match="The URL did not return HTML page"):
        scrape_website("https://example.com/file.pdf")
