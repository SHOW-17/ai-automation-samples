# 02. AI記事自動生成ツール

ココナラサービス: [SEOブログ記事をAIで自動生成するツールを提供します](https://coconala.com/services/4138528)（15,000円）

## このサンプルが示すもの

ココナラで販売している**AI記事自動生成ツール本体の縮小版**です。実際の納品物は同じ構造でカスタマイズして提供しています。

**入力**: キーワード（例: 「Pythonで業務自動化」）
**出力**: SEO構成 → セクション別本文 → メタデータ込みのMarkdown / HTML記事

## 多段階パイプライン

ChatGPTに「記事を書いて」と一発で頼むのとの違い:

```
[1] キーワード分析
       ↓
[2] SEO構成設計（H2 5本 + H3）
       ↓
[3] セクション別本文生成（並列可）
       ↓
[4] メタディスクリプション・タイトル候補生成
       ↓
[5] Markdown / HTML / WordPress対応形式で出力
```

各ステップが独立しているため、品質も一貫性も担保できます。

## 使い方

### 単発生成

```bash
# モック生成（APIキー不要、デモ用）
python generate.py --keyword "Claude Codeで業務自動化" --mock

# 実生成（Anthropic APIキー必要）
export ANTHROPIC_API_KEY=sk-ant-...
python generate.py --keyword "Claude Codeで業務自動化"

# 出力形式指定
python generate.py --keyword "..." --output article.md --format markdown
python generate.py --keyword "..." --output article.html --format html
python generate.py --keyword "..." --format json   # 構造化データとして
```

### 一括生成（CSVから複数キーワード）

```bash
# sample_keywords.csv に書かれたキーワードを順次処理
python bulk_generate.py --keywords sample_keywords.csv --mock --limit 3

# 本番生成、API呼び出し間に2秒待機
python bulk_generate.py --keywords sample_keywords.csv --delay 2.0
```

`bulk_output/_summary.csv` に処理結果のサマリが残ります。

### WordPress自動投稿（オプション）

```bash
# ドライラン（環境変数なしで動作確認）
python wp_post.py --markdown sample_outputs/claude-code-automation.md --dry-run

# 実投稿（draft）
export WP_BASE_URL=https://your-site.example.com
export WP_USERNAME=admin
export WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
python wp_post.py --markdown article.md --status draft

# 公開ステータスで投稿
python wp_post.py --markdown article.md --status publish
```

WordPressの「アプリケーションパスワード」は管理画面のユーザープロフィール末尾から取得できます。

## サンプル出力

`sample_outputs/` に3本の生成済み記事を同梱しています:

1. [Claude Codeで業務自動化を始める3ステップ](sample_outputs/claude-code-automation.md)
2. [Pythonスクレイピングのベストプラクティス2026](sample_outputs/python-scraping.md)
3. [副業で月3万円を稼ぐAI活用ロードマップ](sample_outputs/ai-side-business.md)

## 納品物に含まれるもの（実際のサービス）

- `generate.py` 本体（約400行）
- `prompts/` ジャンル別プロンプトテンプレート集
- `bulk_generate.py` CSV一括処理スクリプト（オプション）
- `wp_post.py` WordPress自動投稿（オプション）
- 画像付きセットアップマニュアル（PDF）
- 初回チャットサポート

## カスタマイズ可能項目（オプション）

| 項目 | 価格 |
|---|---|
| WordPress自動投稿連携 | +5,500円 |
| ジャンル別プロンプト調整 | +5,500円 |
| 画像自動挿入（Unsplash等） | +3,300円 |
| 一括生成スクリプト | +5,500円 |
| 月額保守 | 3,300円/月 |

## API利用料の目安

- GPT-4o-mini: 約5〜15円/記事（3000文字）
- Claude Haiku: 約3〜10円/記事
- Claude Sonnet: 約30〜80円/記事（高品質）

1日10記事生成しても数百円以内に収まります。

## 技術構成

- Python 3.10+
- `anthropic` または `openai` SDK（実生成時）
- 標準ライブラリのみで動くモックモードあり
- 出力フォーマット: Markdown / HTML / JSON
