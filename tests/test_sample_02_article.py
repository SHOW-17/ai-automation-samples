"""sample 02 (AI記事生成) のユニットテスト."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "02-ai-article-generator"
sys.path.insert(0, str(SAMPLE))

import generate  # type: ignore
import wp_post  # type: ignore


def test_mock_generator_produces_article():
    gen = generate.MockGenerator()
    article = generate.build_article("Pythonで業務自動化", gen)
    assert article.title
    assert article.introduction
    assert len(article.sections) == 5
    assert all(s.body for s in article.sections)
    assert article.total_chars() > 1000


def test_to_markdown_has_frontmatter():
    gen = generate.MockGenerator()
    article = generate.build_article("AI", gen)
    md = generate.to_markdown(article)
    assert md.startswith("---")
    assert "title:" in md
    assert "## まとめ" in md


def test_to_html_well_formed():
    gen = generate.MockGenerator()
    article = generate.build_article("AI", gen)
    html = generate.to_html(article)
    assert html.startswith("<!doctype html>")
    assert "<h1>" in html and "</h1>" in html


def test_to_json_parseable():
    import json

    gen = generate.MockGenerator()
    article = generate.build_article("AI", gen)
    parsed = json.loads(generate.to_json(article))
    assert parsed["keyword"] == "AI"
    assert parsed["total_chars"] > 0


def test_wp_parse_frontmatter():
    md = """---
title: Test
description: hello world
---

# Heading

Body here.
"""
    fm, body = wp_post.parse_frontmatter(md)
    assert fm["title"] == "Test"
    assert fm["description"] == "hello world"
    assert "# Heading" in body


def test_wp_parse_no_frontmatter():
    md = "# Just heading\n\nBody"
    fm, body = wp_post.parse_frontmatter(md)
    assert fm == {}
    assert body == md


def test_wp_markdown_to_html_basic():
    html = wp_post.markdown_to_html("# Title\n\n## Subtitle\n\nParagraph **bold** text\n\n- item1\n- item2")
    assert "<h1>Title</h1>" in html
    assert "<h2>Subtitle</h2>" in html
    assert "<strong>bold</strong>" in html
    assert "<ul>" in html and "<li>item1</li>" in html
