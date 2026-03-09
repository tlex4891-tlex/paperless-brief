"""
Scraper modul – stahuje nejnovější články z konfigurovaných PM webů.
"""

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 15


@dataclass
class Article:
    title: str
    url: str
    summary: str = ""
    source: str = ""


@dataclass
class SiteConfig:
    name: str
    url: str
    selector: str
    title_selector: str
    link_selector: str = "self_from_title"
    summary_selector: str = "p"
    date_selector: str = ""
    base_url: str = ""


def fetch_page(url: str) -> str | None:
    """Stáhne HTML stránku."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.warning("Nepodařilo se stáhnout %s: %s", url, exc)
        return None


def _first_match(element, selectors: str) -> BeautifulSoup | None:
    """Zkusí více CSS selektorů oddělených čárkou a vrátí první shodu."""
    for sel in selectors.split(","):
        sel = sel.strip()
        if not sel:
            continue
        match = element.select_one(sel)
        if match:
            return match
    return None


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300] if len(text) > 300 else text


def scrape_site(site: SiteConfig) -> list[Article]:
    """Scrapuje články z jednoho webu."""
    html = fetch_page(site.url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    # Zkusí najít kontejnery článků
    containers = []
    for sel in site.selector.split(","):
        sel = sel.strip()
        if sel:
            containers.extend(soup.select(sel))
    if not containers:
        logger.warning("Žádné články nenalezeny na %s (selektor: %s)", site.url, site.selector)
        return []

    seen_urls = set()

    for container in containers[:10]:  # max 10 kandidátů
        # Najdi titulek
        title_el = _first_match(container, site.title_selector)
        if not title_el:
            continue

        title = _clean_text(title_el.get_text())
        if not title or len(title) < 5:
            continue

        # Najdi odkaz
        link = None
        if site.link_selector == "self_from_title":
            # Odkaz je přímo na titulkovém elementu nebo jeho rodiči <a>
            if title_el.name == "a":
                link = title_el.get("href")
            elif title_el.find("a"):
                link = title_el.find("a").get("href")
            elif title_el.parent and title_el.parent.name == "a":
                link = title_el.parent.get("href")
        else:
            link_el = _first_match(container, site.link_selector)
            if link_el:
                link = link_el.get("href") if link_el.name == "a" else None

        if not link:
            continue

        # Resolve relativní URL
        if link.startswith("/"):
            link = urljoin(site.base_url or site.url, link)

        if link in seen_urls:
            continue
        seen_urls.add(link)

        # Najdi shrnutí
        summary = ""
        if site.summary_selector:
            summary_el = _first_match(container, site.summary_selector)
            if summary_el and summary_el != title_el:
                summary = _clean_text(summary_el.get_text())

        articles.append(Article(
            title=title,
            url=link,
            summary=summary,
            source=site.name,
        ))

    logger.info("Nalezeno %d článků z %s", len(articles), site.name)
    return articles


def scrape_all(sites: list[SiteConfig]) -> dict[str, list[Article]]:
    """Scrapuje všechny konfigurované weby. Vrací dict {site_name: [articles]}."""
    results = {}
    for site in sites:
        logger.info("Scrapuji: %s (%s)", site.name, site.url)
        articles = scrape_site(site)
        results[site.name] = articles
    return results
