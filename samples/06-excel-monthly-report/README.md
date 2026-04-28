# 06. Excel月次レポート自動化

ココナラサービス: [Pythonで業務を自動化します](https://coconala.com/services/3766925)（15,000円〜）の **Excel特化版**

## このサンプルが示すもの

「毎月、各店舗から送られてくるExcelをマージして、本部用の月次レポートを作る」という、**経理・店舗運営で最も頻出する業務**の自動化サンプルです。

**ビフォー**: 5店舗分のExcelを開いて、コピペ集計、別Excelに整形 → 半日仕事
**アフター**: `python monthly_report.py` 1コマンド → 30秒

## 機能

```
[input/store_*.xlsx]  ← 各店舗の月次売上Excel
        ↓
[monthly_report.py]
        ↓
[output/monthly_report.xlsx]
  ├─ サマリシート（KPI + 店舗別売上 + 商品別売上）
  ├─ 店舗別シート × 5
  ├─ 商品別シート（全店舗集計）
  └─ 元データシート（バックアップ）
```

**生成される本部用レポートの中身**:
- 全店舗合計KPI（売上・取引件数・平均客単価・最終取引日）
- 店舗別売上ランキング + 前月比（前月データがあれば）
- 商品別売上TOP20
- カテゴリ別ピボット
- 自動配色・罫線・列幅調整

## 使い方

```bash
# 依存ライブラリのインストール（初回のみ）
pip install openpyxl

# サンプル入力でデモ実行
python monthly_report.py

# 任意のディレクトリのExcelを処理
python monthly_report.py --input-dir /path/to/excels --output report.xlsx

# シート名のカスタマイズ（デフォルトは "売上明細"）
python monthly_report.py --sheet-name "Sales"
```

## 入力Excelの想定フォーマット

各店舗が同じテンプレートで作成している前提:

| date | product | category | quantity | unit_price |
|---|---|---|---|---|
| 2026-04-01 | カフェラテ | ドリンク | 12 | 480 |
| 2026-04-01 | チーズケーキ | フード | 5 | 620 |

ファイル名は `store_<店舗名>.xlsx` 形式（例: `store_shibuya.xlsx`）。

サンプル: `input/store_shibuya.xlsx`, `store_shinjuku.xlsx`, `store_ikebukuro.xlsx`, `store_yokohama.xlsx`, `store_kichijoji.xlsx` の5店舗ぶんを同梱。

## カスタマイズ可能項目

| 項目 | 価格 |
|---|---|
| 入力フォーマットが店舗ごとに異なる場合の正規化 | +5,500円 |
| 前月比・前年同月比の計算ロジック追加 | +3,300円 |
| グラフ自動挿入（折れ線・棒・円） | +5,500円 |
| Slack/メール自動配信 | +5,500円 |
| 月初cron実行設定 | +3,300円 |
| 店舗マスタ・商品マスタの追加 | +5,500円 |

## こういう業務も同じ仕組みで対応可能

- 各支店から送られる経費精算Excelの統合
- 各部門の月次予算実績Excelの集約
- 在庫管理Excelの月次棚卸し集計
- アンケート回答Excelの集計（店舗ごと/部門ごと）

## 技術構成

- Python 3.10+
- `openpyxl` 3.1+ （`pip install openpyxl`）
- 標準ライブラリの `argparse`, `pathlib`, `collections`
- 100行強のメインスクリプト
