"""sample 03 (RSS→SNS) のユニットテスト."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "03-rss-to-social"
sys.path.insert(0, str(SAMPLE))

import pipeline  # type: ignore


def test_auto_hashtags_finds_keywords():
    tags = pipeline.auto_hashtags("Pythonでスクレイピングする方法")
    assert "#Python" in tags
    assert "#スクレイピング" in tags


def test_auto_hashtags_max_limit():
    text = "Python ChatGPT AI Claude 副業 SEO DX 業務自動化 RSS"
    tags = pipeline.auto_hashtags(text, max_tags=3)
    assert len(tags) == 3


def test_truncate_to_x_within_limit():
    short = "短いテキストです"
    result = pipeline.truncate_to_x(short, ["#tag1", "#tag2"])
    assert "#tag1" in result and "#tag2" in result
    assert len(result) <= 140


def test_truncate_to_x_long_text():
    long_text = "あ" * 200
    result = pipeline.truncate_to_x(long_text, ["#tag"])
    assert len(result) <= 140
    assert "…" in result


def test_parse_feed_basic():
    xml = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item><title>Test</title><link>https://example.com/1</link><description>desc</description></item>
  <item><title>Two</title><link>https://example.com/2</link><description>desc2</description></item>
</channel></rss>"""
    items = pipeline.parse_feed(xml)
    assert len(items) == 2
    assert items[0].title == "Test"
    assert items[1].link == "https://example.com/2"


def test_mock_broadcaster_outputs():
    item = pipeline.FeedItem(
        title="Pythonで業務自動化を始めるガイド",
        link="https://example.com/article",
        description="Pythonでの業務自動化",
    )
    gen = pipeline.MockBroadcaster()
    post = gen.generate(item)
    assert post.summary
    assert len(post.x_posts) == 3
    for x in post.x_posts:
        assert len(x["text"]) <= 140
    assert "Python" in post.threads_post
