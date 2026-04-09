from __future__ import annotations

import sys
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import RequestException, Timeout


DEFAULT_TIMEOUT = 10


class ScraperError(Exception):


def validate_url(url:str) -> str:
    cleaned_url = url.strip()
    if not cleaned_url:
        raise ScraperError("The URL cannot be empty")
    parsed_url = urlparse(cleaned_url)
    
    if parsed_url.scheme != "https":
        raise ScraperError("Only HTTPS URLs are allowed")
    
    if not parsed_url.netloc:
        raise ScraperError("Invalid URL Domain request")
    
    return cleaned_url

def fetch_webpage(url:str,timeout:int = DEFAULT_TIMEOUT) -> Response:
    
    validated_url = validate_url(url)
    
    try:
        response = requests.get(validated_url, timeout=timeout)
        response.raise_for_status()
        return response
    
    except Timeout as exc:
        raise ScraperError("Request Timout while fetching webpage") from exc
    
    except RequestException as exc:
        raise ScraperError("Failed to fetch webpage:{exc}") from exc
    
def _extract_meta_description(soup:BeautifulSoup) -> str:
    description_tag = soup.find("meta", attrs= {"name":"description"})
    
    if description_tag and description_tag.get("content"):
        return description_tag["content"].strip()
    
    og_description_tag = soup.find("meta", attrs={"property":"og:description"})
    if og_description_tag and og_description_tag.get("content"):
        return og_description_tag["content"].strip()
    
    return " "

def _extract_links(soup:BeautifulSoup) -> list[str]:
    links:list[str] = []
    
    for tag in soup.find_all("a",href=True):
        href = tag.get("href"," ").strip()
        if href:
            links.append(href)
    
    return links

def _extract_images(soup:BeautifulSoup) -> list[str]:
    images:list[str] = []
    
    for tag in soup.find_all("img",src=True):
        src = tag.get("src"," ").strip()
        if src:
            images.append(src)
    
    return images

def _extract_headings(soup:BeautifulSoup) -> list[str]:
    headings:list[str] = []
    
    for level in ("h1","h2","h3","h4","h5","h6"):
        
        for tag in soup.find_all(level):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
    
    return headings

def parse_html(html:str) -> dict[str,Any]:
    
    soup = BeautifulSoup(html,"html.parser")
    
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else " "
    
    return {
        "title": title,
        "meta_description": _extract_meta_description(soup),
        "links": _extract_links(soup),
        "images": _extract_images(soup),
        "headings": _extract_headings(soup),
    }
    
def scrape_website(url:str, timeout:int = DEFAULT_TIMEOUT) -> dict[str,Any]:
    
    response = fetch_webpage(url,timeout=timeout)
    content_type = response.headers.get("Content_Type"," ")
    
    if "html" not in content_type.lower():
        raise ScraperError("The URL did not return HTML page")
    
    scraped_data = parse_html(response.text)
    
    scraped_data.update(
        {"url": response.url,
         "status_code": response.status_code,
         "content_length": len(response.content),
        }
    )
    return scraped_data


def main() -> int:
    
    if len(sys.argv)!=2:
        print("Usage: python app/scraper.py https://example.com")
        return 1
    
    url = sys.argv[1]
    
    try:
        result = scrape_website(url)
        
    except ScraperError as exc:
        print(f"Error : {exc}")
        return 1
    
    print(f"Status Code :{result['status_code']}")
    print(f"Content Length:{result['content_length'] bytes}")
    print(f"Title: {result['title'] or 'N/A'}")
    print(f"Meta Description:{result['meta_description'] or 'N/A'}")
    print(f"Links Found: {len(result['links'])}")
    print(f"Images Found: {len(result['images'])}")
    print(f"Headings Found: {len(result['headings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
