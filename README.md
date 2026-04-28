# AI Automation Samples

ココナラで提供している5つのサービスの**実物サンプル成果物集**です。
「実際にこういうものが届きます」を見せて、安心して発注いただくための営業材料として公開しています。

提供者: SHOW（[show-smartwork.dev](https://show-smartwork.dev)）

---

## サンプル一覧

| # | サンプル | 対応サービス | 価格 | デモ実行 |
|---|---|---|---:|---|
| 01 | [CSV売上レポート自動生成](samples/01-csv-report-generator/) | [Claude Code開発代行](https://coconala.com/services/4138522) | 30,000円〜 | `python report.py` |
| 02 | [AI記事自動生成ツール](samples/02-ai-article-generator/) | [AI記事自動生成ツール](https://coconala.com/services/4138528) | 15,000円 | `python generate.py --keyword "..." --mock` |
| 03 | [RSS→SNS投稿文生成](samples/03-rss-to-social/) | [AI情報発信自動化](https://coconala.com/services/3806351) | 22,000円 | `python pipeline.py --feed sample_feeds/tech_news.xml --mock` |
| 04 | [複数サイト価格モニタリング](samples/04-price-monitor/) | [Python自動化](https://coconala.com/services/3766925) | 15,000円〜 | `python monitor.py --demo` |
| 05 | [自動化相談 テンプレ集](samples/05-automation-consulting-templates/) | [自動化相談](https://coconala.com/services/3766857) | 3,300円 | Markdown閲覧のみ |
| 06 | [Excel月次レポート自動化](samples/06-excel-monthly-report/) | [Python自動化](https://coconala.com/services/3766925) | 15,000円〜 | `python monthly_report.py` |
| 07 | [LPテンプレート 3種](samples/07-landing-page-template/) | [Claude Code開発代行](https://coconala.com/services/4138522) | 30,000円〜 | ブラウザで `templates/*.html` を開く |

---

## このリポジトリの使い方

### 検討中の方
各サンプルのREADMEと、`output/` 配下に置いてある生成済みアウトプットをご覧ください。
「30,000円で何が届くのか」が具体的にイメージできるはずです。

### 実際に試したい方
ほぼすべてのサンプルが**APIキー不要のモックモード**で動きます。
Python 3.10+ が入っていれば、追加インストールなしで動くものが多いです。

```bash
git clone https://github.com/SHOW-17/ai-automation-samples
cd ai-automation-samples/samples/01-csv-report-generator
python3 report.py
open output/sample_report.html
```

### ご依頼を検討される方
気に入ったサンプルがあれば、対応するココナラサービスからお問い合わせください。
カスタマイズの方向性は各サンプルのREADMEに記載しています。

---

## サービス間の関係

```
                    ┌─────────────────────┐
                    │  自動化相談 ¥3,300   │  ← まずここで方向性を整理
                    │  (No.5)             │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ↓                      ↓                      ↓
┌───────────────┐  ┌──────────────────┐  ┌───────────────────┐
│Python自動化   │  │AI情報発信自動化  │  │AI記事自動生成     │
│¥15,000〜      │  │¥22,000           │  │¥15,000            │
│(No.4)         │  │(No.3)            │  │(No.2)             │
└───────┬───────┘  └────────┬─────────┘  └─────────┬─────────┘
        │                   │                       │
        └──────────┬────────┴───────────────────────┘
                   ↓
       ┌──────────────────────────────┐
       │ Claude Code開発代行 ¥30,000〜 │ ← 上記を含む幅広い開発に対応
       │ (No.1)                       │
       └──────────────────────────────┘
```

---

## 技術スタック

| 言語 | 理由 |
|---|---|
| Python 3.10+ | 配布が楽、依存最小、エンジニア未経験でも引き継ぎやすい |
| 標準ライブラリ中心 | `pip install` 不要で動くサンプルが多い |
| 出力はHTML+Chart.js (CDN) | 社内Slackやメールにそのまま貼れる |

---

## ライセンス

[MIT License](LICENSE) — テンプレート部分は自由にご利用ください。

---

## 連絡先

- ココナラ: https://coconala.com/users/4380829
- ポートフォリオ: https://show-smartwork.dev
- お問い合わせ: ココナラのトークルームから

ご依頼前のご相談・ご質問は無料でお受けしています。お気軽にどうぞ。
