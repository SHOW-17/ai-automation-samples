"""CSVから複数キーワードを読み込んで一括で記事生成する.

使い方:
    python bulk_generate.py --keywords keywords.csv --mock
    python bulk_generate.py --keywords keywords.csv --output-dir bulk_output

CSVの形式: 1列目がキーワード（ヘッダーなしでもOK、行頭が"#"の行は無視）
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

from generate import (
    AnthropicGenerator,
    MockGenerator,
    build_article,
    to_html,
    to_json,
    to_markdown,
)


def load_keywords(path: Path) -> list[str]:
    keywords: list[str] = []
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row:
                continue
            kw = row[0].strip()
            if not kw or kw.startswith("#") or kw.lower() == "keyword":
                continue
            keywords.append(kw)
    return keywords


def slugify(s: str, maxlen: int = 50) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in s)
    return cleaned[:maxlen].strip("_")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keywords", required=True, help="キーワード一覧のCSV")
    parser.add_argument("--output-dir", default="bulk_output")
    parser.add_argument("--format", choices=["markdown", "html", "json"], default="markdown")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--delay", type=float, default=2.0, help="API呼び出し間の待機秒数")
    parser.add_argument("--limit", type=int, default=0, help="処理上限（0で無制限）")
    args = parser.parse_args()

    keywords = load_keywords(Path(args.keywords))
    if args.limit:
        keywords = keywords[: args.limit]
    if not keywords:
        print("[ERR] 有効なキーワードが見つかりません", file=sys.stderr)
        sys.exit(1)
    print(f"[INFO] {len(keywords)}件のキーワードを処理")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mock or not os.environ.get("ANTHROPIC_API_KEY"):
        gen = MockGenerator()
        if not args.mock:
            print("[INFO] APIキー未設定のためモックモード", file=sys.stderr)
    else:
        gen = AnthropicGenerator(os.environ["ANTHROPIC_API_KEY"])

    summary: list[dict] = []
    for i, kw in enumerate(keywords, 1):
        try:
            article = build_article(kw, gen)
            if args.format == "markdown":
                content, ext = to_markdown(article), ".md"
            elif args.format == "html":
                content, ext = to_html(article), ".html"
            else:
                content, ext = to_json(article), ".json"
            fname = f"{i:03d}_{slugify(kw)}{ext}"
            (out_dir / fname).write_text(content, encoding="utf-8")
            chars = article.total_chars()
            print(f"  [{i:3d}/{len(keywords)}] {kw} → {fname} ({chars:,}字)")
            summary.append({"keyword": kw, "file": fname, "chars": chars})
        except Exception as e:
            print(f"  [ERR] {kw}: {e}", file=sys.stderr)
            summary.append({"keyword": kw, "file": "", "chars": 0, "error": str(e)})
        if not args.mock and i < len(keywords):
            time.sleep(args.delay)

    # サマリ書き出し
    summary_path = out_dir / "_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["keyword", "file", "chars", "error"], extrasaction="ignore"
        )
        w.writeheader()
        for r in summary:
            w.writerow(r)

    total = sum(r.get("chars", 0) for r in summary)
    succeed = sum(1 for r in summary if r.get("file"))
    print(f"[OK] 成功 {succeed}/{len(keywords)} / 合計 {total:,}字 / サマリ: {summary_path}")


if __name__ == "__main__":
    main()
