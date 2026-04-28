# 04. 複数サイト価格モニタリングツール

ココナラサービス: [Pythonで業務を自動化します](https://coconala.com/services/3766925)（15,000円〜）

## このサンプルが示すもの

複数のECサイト・比較サイトを定期的にスクレイピングし、**価格変動を検知してアラートを発する**仕組みです。「Pythonで業務自動化」サービスで実際に作成する典型的な成果物の1つ。

**こんな業務に使える**:
- 競合製品の価格変動を毎日チェック
- 自社商品の他店掲載価格を監視（最安値ウォッチ）
- 仕入先の価格変動を早期検知
- 株価・為替・暗号資産の閾値アラート（応用）

## 機能概要

```
[1] watchlist.csv に監視対象URLとセレクタを記述
        ↓
[2] monitor.py 実行（cron可能）
        ↓
[3] 各サイトをスクレイピング → 現在価格取得
        ↓
[4] 履歴 history.csv に追記
        ↓
[5] 前回比で閾値以上の変動があれば alerts.csv + HTMLレポート出力
        ↓
[6] （オプション）Slack / メール通知
```

## 使い方

```bash
# 初回実行（履歴ファイルが作られる）
python monitor.py

# サンプルデータでデモ実行（ローカルHTMLをスクレイプ）
python monitor.py --watchlist sample_data/watchlist.csv

# レポート閲覧
open output/report.html
```

## 入力: watchlist.csv

| name | url | css_selector | threshold_pct |
|---|---|---|---|
| MacBook Air M4 | https://example-shop.com/p/mb-air-m4 | .price | 5 |
| 米5kg | https://supermarket.example.com/rice-5kg | span.price-now | 10 |

`threshold_pct` は変動率（％）の閾値。これを超えるとアラート対象。

## 出力

| ファイル | 内容 |
|---|---|
| `output/history.csv` | 全観測値の時系列ログ |
| `output/alerts.csv` | 閾値超え変動のみ抽出 |
| `output/report.html` | グラフ付きの可視化レポート |

## サンプルデータ

`sample_data/` に以下を同梱:

- `watchlist.csv` — 5商品の監視リスト
- `pages/*.html` — スクレイピング先のローカルHTML（商品ページ模擬）
- `history_30days.csv` — 過去30日分のダミー履歴データ

`monitor.py --demo` でこれらを使ったエンドツーエンドの動作確認ができます。

## カスタマイズ可能項目

| 項目 | 価格 |
|---|---|
| Excel(.xlsx) 出力 | +3,300円 |
| Slack/Discord通知連携 | +5,500円 |
| メール通知（SMTP/SES） | +5,500円 |
| 動的サイト対応（Playwright統合） | +5,500円 |
| 定期実行設定（cron / タスクスケジューラ） | +3,300円 |
| 月額保守・監視追加 | 3,300円/月 |

## 規約・倫理上の注意

- ✅ 公開ページの**人間が読める情報**を、適切な間隔（推奨1秒以上）で取得
- ✅ User-Agentで連絡先を明示
- ✅ robots.txt遵守
- ❌ ログイン後コンテンツの自動取得（規約違反になる場合あり）
- ❌ 短時間の大量リクエスト（業務妨害になりうる）

サービスご利用時は、**監視対象サイトの利用規約を必ず事前に確認**いたします。

## 技術構成

- Python 3.10+
- `requests` + `BeautifulSoup4`（pip install requests beautifulsoup4）
- 標準ライブラリの`csv`, `argparse`, `pathlib`, `datetime`
- 可視化はHTML+Chart.js（CDN）で軽量化
