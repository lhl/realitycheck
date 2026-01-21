"""
Unit tests for scripts/html_extract.py

These tests define the expected behavior for our lightweight HTML extraction:
- Prefer reasonable title/date signals
- Extract main article text while stripping nav/footer noise
- Fall back to common content container classnames
"""

from __future__ import annotations

from html_extract import extract_html


def test_extract_title_prefers_og_title():
    html = """
    <html>
      <head>
        <title>Page Title</title>
        <meta property="og:title" content="OG Title" />
      </head>
      <body><article><p>Hello world</p></article></body>
    </html>
    """
    doc = extract_html(html)
    assert doc.title == "OG Title"


def test_extract_published_date_from_article_published_time_meta():
    html = """
    <html>
      <head>
        <meta property="article:published_time" content="2026-01-21T10:00:00Z" />
      </head>
      <body><article><p>Hello</p></article></body>
    </html>
    """
    doc = extract_html(html)
    assert doc.published == "2026-01-21T10:00:00+00:00"


def test_extract_text_prefers_article_and_strips_nav_footer():
    html = """
    <html>
      <head><title>t</title></head>
      <body>
        <nav>MENU LINKS</nav>
        <article>
          <h1>The pivot</h1>
          <p>Paragraph one.</p>
          <p>Paragraph two.</p>
        </article>
        <footer>FOOTER STUFF</footer>
      </body>
    </html>
    """
    doc = extract_html(html)
    assert "MENU LINKS" not in doc.text
    assert "FOOTER STUFF" not in doc.text
    assert "Paragraph one." in doc.text
    assert "Paragraph two." in doc.text
    assert doc.headings == ["The pivot"]


def test_extract_text_falls_back_to_entry_content_container():
    html = """
    <html>
      <body>
        <div class="sidebar"><p>Ignore me</p></div>
        <div class="entry-content">
          <h1>Entry Title</h1>
          <p>Main content here.</p>
        </div>
      </body>
    </html>
    """
    doc = extract_html(html)
    assert "Ignore me" not in doc.text
    assert "Main content here." in doc.text
