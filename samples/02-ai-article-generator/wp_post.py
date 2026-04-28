"""WordPress REST API への記事投稿（オプション機能のサンプル実装）.

使い方:
    # 環境変数で認証情報を設定
    export WP_BASE_URL=https://your-site.example.com
    export WP_USERNAME=admin
    export WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # WordPressの「アプリケーションパスワード」

    # 単発投稿（ステータスはデフォルト draft）
    python wp_post.py --markdown sample_outputs/claude-code-automation.md

    # 公開ステータスで投稿
    python wp_post.py --markdown article.md --status publish

    # ドライランで動作確認
    python wp_post.py --markdown article.md --dry-run

WordPressのアプリケーションパスワードの取得:
    管理画面 → ユーザー → プロフィール → 一番下の「アプリケーションパスワード」
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """gray-matter風の簡易front-matterパーサ. PyYAML不要."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    fm: dict = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def markdown_to_html(md: str) -> str:
    """超簡易Markdown→HTMLコンバーター（H1-H3、段落、リストのみ）."""
    out: list[str] = []
    in_list = False
    for line in md.splitlines():
        if line.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{line[2:].strip()}</li>")
        elif line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            # bold/italic
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)
            out.append(f"<p>{content}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def post_to_wordpress(
    base_url: str,
    username: str,
    app_password: str,
    title: str,
    content_html: str,
    status: str = "draft",
    excerpt: str = "",
) -> dict:
    auth = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    body = json.dumps(
        {
            "title": title,
            "content": content_html,
            "status": status,
            "excerpt": excerpt,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/wp-json/wp/v2/posts",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERR] WP API: {e.code} {e.reason}", file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--status", choices=["draft", "publish", "private"], default="draft")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    md_text = Path(args.markdown).read_text(encoding="utf-8")
    fm, body = parse_frontmatter(md_text)
    title = fm.get("title") or args.markdown
    excerpt = fm.get("description", "")
    html = markdown_to_html(body)

    if args.dry_run:
        print(f"[DRY-RUN] title='{title}' status='{args.status}'")
        print(f"[DRY-RUN] excerpt='{excerpt[:80]}...'")
        print(f"[DRY-RUN] HTML本文 {len(html):,} 文字")
        print(f"--- HTML preview (head 500) ---\n{html[:500]}")
        return

    base_url = os.environ.get("WP_BASE_URL")
    user = os.environ.get("WP_USERNAME")
    pw = os.environ.get("WP_APP_PASSWORD")
    if not all([base_url, user, pw]):
        print(
            "[ERR] WP_BASE_URL / WP_USERNAME / WP_APP_PASSWORD を環境変数に設定してください.\n"
            "      動作確認は --dry-run で行えます.",
            file=sys.stderr,
        )
        sys.exit(1)

    res = post_to_wordpress(base_url, user, pw, title, html, args.status, excerpt)
    print(f"[OK] 投稿成功: id={res.get('id')} status={res.get('status')} link={res.get('link')}")


if __name__ == "__main__":
    main()
