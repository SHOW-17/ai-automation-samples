"""sample 04 (価格モニタリング) のユニットテスト."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "04-price-monitor"
sys.path.insert(0, str(SAMPLE))

import monitor  # type: ignore


def test_parse_price_strips_yen_and_comma():
    assert monitor.parse_price("¥1,234") == 1234
    assert monitor.parse_price("¥168,000（税込）") == 168000
    assert monitor.parse_price("") is None
    assert monitor.parse_price("無料") is None


def test_extract_naive_class():
    html = '<div><span class="price">¥1,234</span></div>'
    out = monitor._extract_naive(html, ".price")
    assert "1,234" in out


def test_extract_naive_id():
    html = '<div id="price">¥999</div>'
    out = monitor._extract_naive(html, "#price")
    assert "999" in out


def test_detect_alerts_threshold():
    target = monitor.WatchTarget(name="A", url="x", css_selector=".p", threshold_pct=5.0)
    alerts = monitor.detect_alerts([target], current={"A": 1100}, prev={"A": 1000})
    assert len(alerts) == 1
    assert alerts[0]["direction"] == "up"
    assert alerts[0]["diff_pct"] == 10.0


def test_detect_alerts_below_threshold():
    target = monitor.WatchTarget(name="A", url="x", css_selector=".p", threshold_pct=15.0)
    alerts = monitor.detect_alerts([target], current={"A": 1100}, prev={"A": 1000})
    assert alerts == []


def test_detect_alerts_handles_none():
    target = monitor.WatchTarget(name="A", url="x", css_selector=".p", threshold_pct=5.0)
    assert monitor.detect_alerts([target], current={"A": None}, prev={"A": 1000}) == []
    assert monitor.detect_alerts([target], current={"A": 1000}, prev={"A": None}) == []
