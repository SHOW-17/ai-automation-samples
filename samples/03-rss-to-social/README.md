# 03. RSS → SNS投稿文 自動生成

ココナラサービス: [AIで完全自動！情報発信の仕組みを構築します](https://coconala.com/services/3806351)（22,000円）

## このサンプルが示すもの

「情報発信を毎日手動でやっていて時間がない」を解決する仕組みのコア部分です。RSSフィードから新着記事を取得し、AIで以下を自動生成します:

- 200字程度の**要約文**
- **X投稿文 3パターン**（カジュアル / フォーマル / 質問形式）
- **Threads投稿文** 1本（X版より長め、絵文字あり）
- **note向け紹介文**（300字）

## なぜRSS起点なのか

X/Threads/noteへの「自動投稿」を実装することは技術的には可能ですが、**プラットフォーム規約のリスクが高い**領域です。本サービスでは投稿の自動化はあえてスコープから外し、**「ネタ集め → 投稿文の下書き生成」までを自動化**する方針を取っています。

- ✅ RSS取得・要約・投稿文生成 → 完全自動
- 🟡 投稿そのもの → 手動（スマホで5秒）or 公式API利用

これにより、品質チェックを人間が挟みつつ、面倒な「ネタ出し」と「文章を考える」作業から解放されます。

## 使い方

```bash
# モック生成（API不要）
python pipeline.py --feed sample_feeds/tech_news.xml --mock

# 実生成
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline.py --feed https://example.com/rss

# 出力先指定
python pipeline.py --feed sample_feeds/tech_news.xml --mock --output posts.json
```

## 入力: RSS / Atomフィード

公開されているRSSフィードURLを直接指定するか、ローカルのXMLファイルを指定。

`sample_feeds/tech_news.xml` にダミーフィード（5記事）を同梱。

## 出力: JSON / Markdown / HTML

各記事に対して、以下の構造で出力されます:

```json
{
  "source": "https://example.com/article-1",
  "title": "...",
  "summary": "...（200字）",
  "x_posts": [
    {"variant": "casual", "text": "..."},
    {"variant": "formal", "text": "..."},
    {"variant": "question", "text": "..."}
  ],
  "threads_post": "...",
  "note_intro": "..."
}
```

`output/sample_posts.html` を開くと、コピペしやすい一覧UIが表示されます。

## 実際の運用フロー

```
[毎朝6:00 cron]
  ↓
[RSS取得]
  ↓
[AI生成 → JSON保存]
  ↓
[HTMLレポートをSlack/メールで配信]
  ↓
[人間がスマホで確認 → 良いものだけ手動投稿]
```

## カスタマイズ可能項目

| 項目 | 価格 |
|---|---|
| カスタムRSS（複数フィード統合・フィルタ条件） | +5,500円 |
| Slack/Discord自動配信 | +5,500円 |
| ハッシュタグ自動付与 | +3,300円 |
| 画像自動生成連携 | +5,500円 |
| 月額保守 | 3,300円/月 |

## 規約リスクへの注意（重要）

- ❌ Threads, note等のスクレイピングによる自動投稿は**規約違反**です
- ✅ 公式APIが提供されているX/Twitterのみ自動投稿可能
- ✅ それ以外は「下書き生成」までで止め、投稿は手動

このサンプルは**規約リスクを避けた設計**になっています。受託時にも同じ方針でご提案します。
