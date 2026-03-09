"""
Newsletter generátor – vytváří HTML newsletter z nascrapovaných článků.
"""

import os
from datetime import datetime

from jinja2 import Template

from scraper import Article

NEWSLETTER_TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
  /* Reset */
  body, h1, h2, h3, p { margin: 0; padding: 0; }

  body {
    background: #0c0e11;
    color: #e8eaf0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 300;
    line-height: 1.6;
    padding: 0;
  }

  .wrapper {
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 24px;
  }

  /* Header */
  .header {
    text-align: center;
    padding-bottom: 32px;
    border-bottom: 1px solid #1e2329;
    margin-bottom: 40px;
  }

  .header h1 {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 28px;
    font-weight: 900;
    color: #c9a84c;
    letter-spacing: 0.02em;
    margin-bottom: 8px;
  }

  .header .subtitle {
    color: #5c6470;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .header .date {
    color: #8a919e;
    font-size: 13px;
    margin-top: 6px;
    font-family: 'IBM Plex Mono', monospace;
  }

  /* Article card */
  .article-card {
    background: #13161a;
    border: 1px solid #1e2329;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 20px;
    transition: border-color 0.2s;
  }

  .article-card:hover {
    border-color: #2a3040;
  }

  .source-badge {
    display: inline-block;
    background: #1a2d45;
    color: #4a8fd4;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
  }

  .article-card h2 {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 8px;
    line-height: 1.4;
  }

  .article-card h2 a {
    color: #e8eaf0;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s, color 0.2s;
  }

  .article-card h2 a:hover {
    color: #c9a84c;
    border-bottom-color: #c9a84c;
  }

  .article-card .summary {
    color: #8a919e;
    font-size: 14px;
    line-height: 1.55;
    margin-bottom: 12px;
  }

  .read-more {
    display: inline-block;
    color: #3dba7e;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    letter-spacing: 0.03em;
  }

  .read-more:hover {
    color: #4de89a;
  }

  .read-more::after {
    content: ' →';
  }

  /* Footer */
  .footer {
    text-align: center;
    padding-top: 32px;
    border-top: 1px solid #1e2329;
    margin-top: 40px;
    color: #5c6470;
    font-size: 12px;
  }

  .footer a {
    color: #5c6470;
    text-decoration: underline;
  }

  /* Empty state */
  .empty-state {
    text-align: center;
    padding: 40px;
    color: #5c6470;
  }

  .empty-state .icon {
    font-size: 48px;
    margin-bottom: 12px;
  }
</style>
</head>
<body>

<div class="wrapper">
  <div class="header">
    <h1>{{ title }}</h1>
    <div class="subtitle">{{ subtitle }}</div>
    <div class="date">{{ date }}</div>
  </div>

  {% if articles %}
    {% for article in articles %}
    <div class="article-card">
      <span class="source-badge">{{ article.source }}</span>
      <h2><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></h2>
      {% if article.summary %}
      <p class="summary">{{ article.summary }}</p>
      {% endif %}
      <a href="{{ article.url }}" class="read-more" target="_blank" rel="noopener">Číst článek</a>
    </div>
    {% endfor %}
  {% else %}
    <div class="empty-state">
      <div class="icon">📭</div>
      <p>Tento týden nebyly nalezeny žádné nové články.</p>
    </div>
  {% endif %}

  <div class="footer">
    <p>Paperless Brief &mdash; automaticky generovaný přehled</p>
    <p>Vytvořeno {{ generated_at }}</p>
  </div>
</div>

</body>
</html>"""


def pick_best_articles(
    site_articles: dict[str, list[Article]],
    max_per_site: int = 1,
) -> list[Article]:
    """Vybere nejzajímavější článek z každého webu.

    Heuristika: preferuje články s delším shrnutím (více informací),
    a titulky, které nejsou příliš krátké.
    """
    picked = []
    for site_name, articles in site_articles.items():
        if not articles:
            continue

        # Skóre: délka titulku + délka shrnutí (proxy pro "zajímavost")
        scored = sorted(
            articles,
            key=lambda a: len(a.title) + len(a.summary) * 2,
            reverse=True,
        )
        picked.extend(scored[:max_per_site])

    return picked


def generate_newsletter(
    articles: list[Article],
    title: str = "Paperless Brief – Týdenní PM Přehled",
    subtitle: str = "Nejlepší články z oblasti projektového řízení",
) -> str:
    """Vygeneruje HTML newsletter."""
    now = datetime.now()
    template = Template(NEWSLETTER_TEMPLATE)
    return template.render(
        title=title,
        subtitle=subtitle,
        date=f"Týden {now.isocalendar()[1]} / {now.year}",
        articles=articles,
        generated_at=now.strftime("%d. %m. %Y v %H:%M"),
    )


def save_newsletter(html: str, output_dir: str, filename_template: str) -> str:
    """Uloží newsletter do souboru. Vrací cestu k souboru."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = filename_template.replace("{date}", date_str)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
