"""RSSフィード → 要約 → X/Threads/note投稿文の自動生成パイプライン.

使い方:
    python pipeline.py --feed sample_feeds/tech_news.xml --mock
    python pipeline.py --feed https://example.com/rss

出力: JSON, Markdown, HTML（モバイルで確認しやすいレイアウト）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


# --------------- フィードパース ---------------


@dataclass
class FeedItem:
    title: str
    link: str
    description: str
    published: str = ""


def fetch_feed_xml(source: str, timeout: float = 15.0, retries: int = 2) -> str:
    if not source.startswith("http"):
        return Path(source).read_text(encoding="utf-8")
    last_err: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            req = urllib.request.Request(
                source,
                headers={
                    "User-Agent": "rss-to-social/1.0 (+https://github.com/SHOW-17/ai-automation-samples)"
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            wait = 2 ** (attempt - 1)
            print(
                f"[WARN] フィード取得失敗 (試行 {attempt}/{retries + 1}): {e}. {wait}秒待機",
                file=sys.stderr,
            )
            time.sleep(wait)
    raise RuntimeError(f"フィード取得失敗: {source} ({last_err})")


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_feed(xml_text: str) -> list[FeedItem]:
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []
    # RSS 2.0
    for it in root.iter():
        if _strip_ns(it.tag) in ("item", "entry"):
            title = link = desc = pub = ""
            for child in it:
                t = _strip_ns(child.tag)
                if t == "title":
                    title = (child.text or "").strip()
                elif t == "link":
                    link = (child.attrib.get("href") or child.text or "").strip()
                elif t in ("description", "summary", "content"):
                    desc = (child.text or "").strip()
                elif t in ("pubDate", "published", "updated"):
                    pub = (child.text or "").strip()
            if title or link:
                items.append(FeedItem(title=title, link=link, description=desc, published=pub))
    return items


# --------------- 生成エンジン ---------------


@dataclass
class GeneratedPost:
    source: str
    title: str
    summary: str
    x_posts: list[dict] = field(default_factory=list)
    threads_post: str = ""
    note_intro: str = ""


_HASHTAG_KEYWORDS = {
    "Claude": "#ClaudeCode",
    "Python": "#Python",
    "AI": "#AI",
    "ChatGPT": "#ChatGPT",
    "副業": "#副業",
    "業務自動化": "#業務自動化",
    "スクレイピング": "#スクレイピング",
    "RSS": "#RSS",
    "SEO": "#SEO",
    "DX": "#DX",
}


def auto_hashtags(text: str, max_tags: int = 3) -> list[str]:
    """テキストから関連キーワードを拾って#タグを生成（重複排除）."""
    found: list[str] = []
    seen: set[str] = set()
    for kw, tag in _HASHTAG_KEYWORDS.items():
        if kw in text and tag not in seen:
            found.append(tag)
            seen.add(tag)
            if len(found) >= max_tags:
                break
    return found


def truncate_to_x(text: str, hashtags: list[str], max_len: int = 140) -> str:
    """X(Twitter)の文字数制限を考慮して末尾にハッシュタグを足す."""
    suffix = ("\n" + " ".join(hashtags)) if hashtags else ""
    available = max_len - len(suffix)
    if len(text) > available:
        text = text[: available - 1].rstrip() + "…"
    return text + suffix


class MockBroadcaster:
    """API無しでテンプレートから投稿文を生成（デモ用）."""

    def generate(self, item: FeedItem) -> GeneratedPost:
        title = item.title or "（無題）"
        topic = re.split(r"[—|│:：]", title)[0].strip()[:30]
        tags = auto_hashtags(title + " " + (item.description or ""))

        summary = (
            f"{title}に関する記事です。本記事では{topic}の最新動向と実践的な活用法について、"
            f"具体的な事例を交えながら解説しています。記事中で示されている観点は、"
            f"特に2026年現在のトレンドを押さえる上で参考になる内容です。"
        )

        x_casual = truncate_to_x(
            f"ちょっと面白い記事見つけた👀\n「{topic}」って結局どこから始めるのが正解なのか、わかりやすくまとまってる。\n{item.link}",
            tags,
        )
        x_formal = truncate_to_x(
            f"【{topic}】に関する記事を読みました。実務で押さえておくべきポイントが体系的に整理されており、学びの多い内容でした。\n{item.link}",
            tags,
        )
        x_question = truncate_to_x(
            f"質問です。{topic}についてみなさんはどう取り組まれていますか？\nこちらの記事の整理が参考になりました👇\n{item.link}",
            tags,
        )

        threads = (
            f"📌 {title}\n\n"
            f"{topic}について、改めて整理されている良記事だった。\n\n"
            f"特に印象に残ったのは「最初から完璧を目指さず、70%の完成度で動かしながら学ぶ」という考え方。"
            f"この姿勢が結局いちばん効率がいいんだなと再認識。\n\n"
            f"全文はこちら👇\n{item.link}"
        )

        note_intro = (
            f"今日読んだ記事「{title}」がとても良かったので、自分なりの解釈と一緒にメモしておきます。"
            f"{topic}に取り組み始めた人が最初につまずきがちなポイントが、丁寧に整理されている記事でした。"
            f"以下、特に参考になった3つの観点について、私自身の経験も踏まえて補足します。"
        )

        return GeneratedPost(
            source=item.link,
            title=title,
            summary=summary,
            x_posts=[
                {"variant": "casual", "text": x_casual},
                {"variant": "formal", "text": x_formal},
                {"variant": "question", "text": x_question},
            ],
            threads_post=threads,
            note_intro=note_intro,
        )


class AnthropicBroadcaster:
    """実APIでバリエーションを生成. anthropic SDK必要."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        try:
            import anthropic  # type: ignore
        except ImportError:
            print("anthropic未インストール: pip install anthropic", file=sys.stderr)
            sys.exit(1)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _ask(self, system: str, user: str, max_tokens: int = 800) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()

    def generate(self, item: FeedItem) -> GeneratedPost:
        prompt = (
            f"次の記事を元に、SNS投稿用テキストをJSONで返してください。\n\n"
            f"タイトル: {item.title}\nURL: {item.link}\n説明: {item.description[:400]}\n\n"
            "JSON形式: {"
            '"summary": "200字程度の要約", '
            '"x_posts": [{"variant":"casual","text":"..."},{"variant":"formal","text":"..."},{"variant":"question","text":"..."}], '
            '"threads_post": "Threads向け本文（300-500字、絵文字あり、URL末尾）", '
            '"note_intro": "note記事の冒頭300字"}'
            "X投稿は140字以内、URL含む。JSONのみ返答。"
        )
        text = self._ask("あなたはSNS運用の専門家です。読者に届く言葉で書きます。", prompt, 1500)
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```")
        data = json.loads(text)
        return GeneratedPost(
            source=item.link,
            title=item.title,
            summary=data["summary"],
            x_posts=data["x_posts"],
            threads_post=data["threads_post"],
            note_intro=data["note_intro"],
        )


# --------------- 出力 ---------------


def to_json(posts: list[GeneratedPost]) -> str:
    return json.dumps(
        [
            {
                "source": p.source,
                "title": p.title,
                "summary": p.summary,
                "x_posts": p.x_posts,
                "threads_post": p.threads_post,
                "note_intro": p.note_intro,
            }
            for p in posts
        ],
        ensure_ascii=False,
        indent=2,
    )


def to_html(posts: list[GeneratedPost]) -> str:
    cards = []
    for i, p in enumerate(posts):
        x_blocks = "".join(
            f'<div class="post"><span class="tag">X / {x["variant"]}</span>'
            f'<button class="copy" data-text="{_esc_attr(x["text"])}">コピー</button>'
            f'<pre>{_esc(x["text"])}</pre></div>'
            for x in p.x_posts
        )
        cards.append(f"""
<article class="card">
  <h2>{i+1}. {_esc(p.title)}</h2>
  <p class="src"><a href="{_esc(p.source)}" target="_blank">{_esc(p.source)}</a></p>
  <h3>要約</h3><p>{_esc(p.summary)}</p>
  <h3>X 投稿候補</h3>{x_blocks}
  <h3>Threads</h3>
  <div class="post"><button class="copy" data-text="{_esc_attr(p.threads_post)}">コピー</button>
  <pre>{_esc(p.threads_post)}</pre></div>
  <h3>note 冒頭</h3>
  <div class="post"><button class="copy" data-text="{_esc_attr(p.note_intro)}">コピー</button>
  <pre>{_esc(p.note_intro)}</pre></div>
</article>""")
    cards_html = "\n".join(cards)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<title>SNS投稿候補 ({generated})</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ font-family: -apple-system, "Hiragino Sans", system-ui, sans-serif; max-width: 720px; margin: 16px auto; padding: 0 12px; background: #f5f7fa; color: #1f2937; line-height: 1.7; }}
h1 {{ font-size: 22px; }}
.card {{ background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
.card h2 {{ margin: 0 0 4px; font-size: 16px; }}
.card h3 {{ margin-top: 16px; margin-bottom: 4px; font-size: 13px; color: #6b7280; }}
.src a {{ font-size: 12px; color: #2563eb; word-break: break-all; }}
.post {{ position: relative; }}
.tag {{ display: inline-block; background: #2563eb; color: white; font-size: 11px; padding: 2px 8px; border-radius: 999px; margin-bottom: 4px; }}
.post pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; font-family: inherit; font-size: 14px; margin: 4px 0 12px; }}
.copy {{ position: absolute; top: 0; right: 0; font-size: 11px; padding: 4px 8px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; cursor: pointer; }}
.copy:hover {{ background: #f3f4f6; }}
</style></head><body>
<h1>SNS投稿候補（{generated} 生成）</h1>
{cards_html}
<script>
document.querySelectorAll('.copy').forEach(b => b.addEventListener('click', () => {{
  navigator.clipboard.writeText(b.dataset.text);
  const orig = b.textContent;
  b.textContent = 'コピー済';
  setTimeout(() => b.textContent = orig, 1200);
}}));
</script>
</body></html>"""


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _esc_attr(s: str) -> str:
    return _esc(s).replace('"', "&quot;").replace("\n", "&#10;")


# --------------- CLI ---------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["html", "json"], default="html")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    xml = fetch_feed_xml(args.feed)
    items = parse_feed(xml)[: args.limit]
    print(f"[INFO] {len(items)}件の記事を取得", file=sys.stderr)

    if args.mock or not os.environ.get("ANTHROPIC_API_KEY"):
        gen = MockBroadcaster()
        if not args.mock:
            print("[INFO] APIキー未設定、モックモード", file=sys.stderr)
    else:
        gen = AnthropicBroadcaster(os.environ["ANTHROPIC_API_KEY"])

    posts = [gen.generate(it) for it in items]

    if args.format == "json":
        out = to_json(posts)
        ext = "json"
    else:
        out = to_html(posts)
        ext = "html"

    out_path = Path(args.output) if args.output else Path(f"output/sample_posts.{ext}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"[OK] {len(posts)}件 → {out_path}")


if __name__ == "__main__":
    main()
