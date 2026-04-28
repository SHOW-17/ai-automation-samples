"""キーワードからSEO最適化された記事を多段階で自動生成する.

使い方:
    python generate.py --keyword "Pythonで業務自動化" --mock
    python generate.py --keyword "Pythonで業務自動化"  # ANTHROPIC_API_KEY 必要

実装方針:
    [1] キーワード→構成（H2 5本 + 各H3 2-3本）
    [2] 各H2セクションの本文生成
    [3] メタタイトル・ディスクリプション生成
    [4] Markdown / HTML / JSON で出力
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# --------------- データ構造 ---------------


@dataclass
class Section:
    h2: str
    h3_list: list[str] = field(default_factory=list)
    body: str = ""


@dataclass
class Article:
    keyword: str
    title: str
    meta_description: str
    introduction: str
    sections: list[Section]
    conclusion: str
    generated_at: str

    def total_chars(self) -> int:
        n = len(self.title) + len(self.meta_description) + len(self.introduction) + len(self.conclusion)
        for s in self.sections:
            n += len(s.h2) + len(s.body) + sum(len(h) for h in s.h3_list)
        return n


# --------------- 生成エンジン（モック） ---------------


class MockGenerator:
    """API無しでも動くテンプレートベースの生成器（デモ用）."""

    def outline(self, keyword: str) -> tuple[str, list[Section]]:
        title = f"【完全ガイド】{keyword}を最短で実現する5つのステップ"
        sections = [
            Section(
                h2=f"{keyword}とは？基本的な考え方",
                h3_list=[
                    f"{keyword}が注目される背景",
                    f"{keyword}に向いているケース",
                    "始める前に押さえる3つの前提",
                ],
            ),
            Section(
                h2="必要なツールと環境構築",
                h3_list=["最低限揃えておくツール", "推奨セットアップ手順", "よくある初期トラブル"],
            ),
            Section(
                h2="実践ステップ — 最初の1週間でやること",
                h3_list=["Day1-2: 現状把握", "Day3-5: 試作と検証", "Day6-7: 本番への展開"],
            ),
            Section(
                h2="運用を継続するためのコツ",
                h3_list=["KPIの設定方法", "失敗から学ぶ3つの教訓"],
            ),
            Section(
                h2="さらに伸ばすための応用",
                h3_list=["他ツールとの連携", "自動化の次のステップ"],
            ),
        ]
        return title, sections

    def section_body(self, keyword: str, section: Section) -> str:
        bodies: list[str] = []
        bodies.append(
            f"このセクションでは「{section.h2}」というテーマで、{keyword}に取り組む際の実践的なポイントを解説します。"
            f"単なる概念の説明ではなく、現場で使える具体的なアプローチを中心にまとめています。"
        )
        for i, h3 in enumerate(section.h3_list, 1):
            bodies.append(f"\n### {h3}\n")
            bodies.append(
                f"{h3}を考えるうえで重要なのは、{keyword}の本質を理解したうえで現実の制約と向き合うことです。"
                f"多くの人が陥りがちなのは、ツールの選定にばかり時間をかけて、本来の目的を見失ってしまうパターンです。"
            )
            bodies.append(
                f"具体的なアクションとしては、まず小さく始めて、結果を計測し、改善のサイクルを回すことが基本になります。"
                f"特に{keyword}のような領域では、最初から完璧を目指すより、70%の完成度で動かしながら学ぶ方が早く成果が出ます。"
            )
            if i == len(section.h3_list):
                bodies.append(
                    f"このプロセスを繰り返すことで、{keyword}に関するノウハウが蓄積され、より高度な活用へとつながっていきます。"
                )
        return "\n".join(bodies)

    def meta(self, keyword: str, title: str) -> str:
        return f"{keyword}の始め方を5ステップで解説。必要なツール・環境構築・運用のコツまでまとめた完全ガイド。初心者が最短で成果を出すためのロードマップ付き。"

    def intro(self, keyword: str) -> str:
        return (
            f"「{keyword}に興味はあるけれど、何から始めればいいかわからない」——そんな方は多いのではないでしょうか。"
            f"本記事では、{keyword}を最短で形にするための5つのステップを、必要なツール・運用のコツ・よくあるつまずきまで含めて解説します。"
            f"読み終える頃には、明日から動き出せる状態になっているはずです。"
        )

    def conclusion(self, keyword: str) -> str:
        return (
            f"ここまで、{keyword}を実現するための5ステップを解説してきました。"
            f"重要なのは、いきなり完璧を目指さず、小さく始めて改善を回すこと。"
            f"この記事をきっかけに、あなたの環境で{keyword}が動き始めることを願っています。"
        )


# --------------- 生成エンジン（Anthropic API） ---------------


class AnthropicGenerator:
    """実APIを使う生成器. anthropic パッケージが必要."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        try:
            import anthropic  # type: ignore
        except ImportError:
            print("anthropic パッケージが未インストールです: pip install anthropic", file=sys.stderr)
            sys.exit(1)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _ask(self, system: str, user: str, max_tokens: int = 1500) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")

    def outline(self, keyword: str) -> tuple[str, list[Section]]:
        prompt = (
            f"キーワード「{keyword}」でSEO記事を書きます。"
            "JSONで以下を返してください: "
            '{"title": "魅力的な記事タイトル", "sections": [{"h2": "...", "h3": ["...", "..."]}, ...]}'
            "h2は5本、各h2に対してh3は2-3本。タイトルはクリックされやすい32文字程度で。JSONだけ返答。"
        )
        text = self._ask("あなたはSEO記事の構成設計のプロです。", prompt)
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```")
        data = json.loads(text)
        sections = [Section(h2=s["h2"], h3_list=s.get("h3", [])) for s in data["sections"]]
        return data["title"], sections

    def section_body(self, keyword: str, section: Section) -> str:
        h3_list = "\n".join(f"- {h}" for h in section.h3_list)
        prompt = (
            f"キーワード「{keyword}」のSEO記事を書いています。\n"
            f"H2: {section.h2}\n"
            f"H3:\n{h3_list}\n\n"
            "このH2セクションの本文をMarkdownで書いてください。各H3を見出しにしてその下に2-3段落書く。"
            "全体で800-1200文字。装飾的な前置きは不要、本文のみ返答。"
        )
        return self._ask("あなたはプロのSEOライターです。読者目線で具体的に書きます。", prompt, 2000)

    def meta(self, keyword: str, title: str) -> str:
        prompt = f"記事タイトル「{title}」のメタディスクリプションを120文字程度で1文だけ。装飾なし、本文のみ。"
        return self._ask("SEOコピーライター", prompt, 200).strip()

    def intro(self, keyword: str) -> str:
        prompt = f"キーワード「{keyword}」のSEO記事のリード文を200-300文字で。読者の悩みに共感し、本記事で得られることを示す。本文のみ返答。"
        return self._ask("SEOライター", prompt, 600).strip()

    def conclusion(self, keyword: str) -> str:
        prompt = f"キーワード「{keyword}」のSEO記事のまとめを150-200文字で。読者の次のアクションを後押しする内容。本文のみ返答。"
        return self._ask("SEOライター", prompt, 500).strip()


# --------------- パイプライン ---------------


def build_article(keyword: str, gen) -> Article:
    title, sections = gen.outline(keyword)
    for s in sections:
        s.body = gen.section_body(keyword, s)
    intro = gen.intro(keyword)
    conclusion = gen.conclusion(keyword)
    meta_desc = gen.meta(keyword, title)
    return Article(
        keyword=keyword,
        title=title,
        meta_description=meta_desc,
        introduction=intro,
        sections=sections,
        conclusion=conclusion,
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )


# --------------- 出力フォーマッタ ---------------


def to_markdown(a: Article) -> str:
    parts = [
        "---",
        f"title: {a.title}",
        f"description: {a.meta_description}",
        f"keyword: {a.keyword}",
        f"generated_at: {a.generated_at}",
        "---",
        "",
        f"# {a.title}",
        "",
        a.introduction,
        "",
    ]
    for s in a.sections:
        parts.append(f"## {s.h2}")
        parts.append("")
        parts.append(s.body)
        parts.append("")
    parts.append("## まとめ")
    parts.append("")
    parts.append(a.conclusion)
    return "\n".join(parts)


def to_html(a: Article) -> str:
    body_html = [f"<h1>{a.title}</h1>", f"<p>{a.introduction}</p>"]
    for s in a.sections:
        body_html.append(f"<h2>{s.h2}</h2>")
        for line in s.body.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("### "):
                body_html.append(f"<h3>{line[4:]}</h3>")
            else:
                body_html.append(f"<p>{line}</p>")
    body_html.append("<h2>まとめ</h2>")
    body_html.append(f"<p>{a.conclusion}</p>")
    body = "\n".join(body_html)
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8">
<title>{a.title}</title>
<meta name="description" content="{a.meta_description}">
<style>
  body {{ font-family: -apple-system, "Hiragino Sans", system-ui, sans-serif; max-width: 720px; margin: 32px auto; padding: 0 16px; line-height: 1.8; color: #1f2937; }}
  h1 {{ font-size: 26px; }}
  h2 {{ margin-top: 32px; padding-bottom: 8px; border-bottom: 2px solid #2563eb; }}
  h3 {{ margin-top: 24px; color: #374151; }}
  p {{ margin: 16px 0; }}
</style></head><body>
{body}
</body></html>"""


def to_json(a: Article) -> str:
    return json.dumps(
        {
            "keyword": a.keyword,
            "title": a.title,
            "meta_description": a.meta_description,
            "introduction": a.introduction,
            "sections": [{"h2": s.h2, "h3_list": s.h3_list, "body": s.body} for s in a.sections],
            "conclusion": a.conclusion,
            "generated_at": a.generated_at,
            "total_chars": a.total_chars(),
        },
        ensure_ascii=False,
        indent=2,
    )


# --------------- CLI ---------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["markdown", "html", "json"], default="markdown")
    parser.add_argument("--mock", action="store_true", help="API無しのテンプレ生成")
    args = parser.parse_args()

    if args.mock or not os.environ.get("ANTHROPIC_API_KEY"):
        if not args.mock:
            print("[INFO] ANTHROPIC_API_KEYが未設定のためモックモードで生成", file=sys.stderr)
        gen = MockGenerator()
    else:
        gen = AnthropicGenerator(os.environ["ANTHROPIC_API_KEY"])

    article = build_article(args.keyword, gen)

    if args.format == "markdown":
        out = to_markdown(article)
        ext = ".md"
    elif args.format == "html":
        out = to_html(article)
        ext = ".html"
    else:
        out = to_json(article)
        ext = ".json"

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"[OK] {len(out):,}文字 → {args.output}")
    else:
        slug = "".join(c if c.isalnum() else "_" for c in args.keyword)[:40]
        default_path = Path(f"output/{slug}{ext}")
        default_path.parent.mkdir(parents=True, exist_ok=True)
        default_path.write_text(out, encoding="utf-8")
        print(f"[OK] {len(out):,}文字 → {default_path}")


if __name__ == "__main__":
    main()
