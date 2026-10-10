# 08. n8n 問い合わせ自動化ワークフロー

対応サービス: n8n で SaaS・API 連携を自動化（ココナラ・準備中）

## このサンプルが示すもの

問い合わせを受け取ったら **分類 → 表に記録 → チャットに通知** までを自動で行う、n8n のワークフローです。
n8n の出品でお渡しする納品物（ワークフローのファイル・取り込みと接続の手順書・エラーの確認方法）と同じ形にしてあります。

当方の検証環境（n8n 2.42.6 をローカルで起動）で、下の「動作確認の手順」のとおり実際に動かしています。
その結果は `output/` に入っています。

```
[問い合わせを受信]  Webhook（POST /webhook/inquiry）
        ↓
[入力チェック]      氏名・件名・本文が空ならエラーにして止める
        ↓
[AI分類（Anthropic）] ← 初期状態は無効。APIキーを入れると有効にできる
        ↓
[分類]              AI の答え、または キーワード判定で「見積り依頼／不具合／その他」に分ける
        ↓
[表に記録]          n8n の Data table「inquiries」に1行追加
        ↓
[チャットに通知]    Slack と同じ形式（{"text": "..."}）で HTTP 送信
        ↓
[受付結果を返す]    呼び出し元に分類結果を返す

（どこかで失敗したら）
[エラーを受け取る] → [通知文を作る] → [チャットに通知]   ← 別ワークフロー（Error Trigger）
```

## ファイル

| ファイル | 内容 |
|---|---|
| `workflows/inquiry-workflow.json` | 本体のワークフロー（7ノード） |
| `workflows/error-notify-workflow.json` | エラー通知用ワークフロー（Error Trigger・3ノード） |
| `sample_requests/*.json` | 動作確認用の問い合わせ（ダミー）。`99_` は本文が空で、わざと失敗させる用 |
| `send_samples.sh` | `sample_requests/` を順に Webhook へ送る curl スクリプト |
| `tools/dummy_chat_receiver.py` | Slack の代わりに通知を受けるローカルの受け口（127.0.0.1 だけで待ち受け） |
| `tools/sanitize_export.py` | エクスポートした JSON から、アカウント情報や認証情報を取り除いて確認する |
| `output/` | 検証環境で実際に動かした結果（下の「実行結果」） |

## 1. 取り込み方（Import from file）

1. n8n を開き、左上の「＋」→ **Workflow** で空のワークフローを作る
2. 画面上部の「…」メニュー → **Import** → **From file** で `error-notify-workflow.json` を選ぶ → 保存
3. もう1つ空のワークフローを作り、同じ手順で `inquiry-workflow.json` を取り込む → 保存
4. 本体ワークフローの「…」→ **Settings** → **Error workflow** で、手順2のエラー通知用ワークフローを選ぶ
   （ファイルに書いてある ID は当方の環境のものなので、取り込んだ先では選び直しが要ります）
5. 表を作る: 左メニューの **Overview** → **Data tables** → **Create data table**。名前は `inquiries`、
   列は `received_at` `name` `email` `subject` `body` `category` `classifier`（すべて文字列）
6. 本体ワークフローを **Publish**（公開）する。公開しないと本番用の Webhook URL は動きません

## 2. 接続の設定

### AI 分類（Anthropic / OpenAI）— お客様名義の API キーを入れる

初期状態では「AI分類（Anthropic）」ノードは**無効**で、「分類」ノードのキーワード判定で分けます（APIキー不要）。
AI で分類する場合は、**お客様名義の API キー**を使います（当方はキーをお預かりしません。利用料金はお客様のご負担です）。

1. 左メニューの **Credentials** → **Create credential** → **Anthropic** を選び、API キーを登録
2. 「AI分類（Anthropic）」ノードを開き、手順1の認証情報を選ぶ。**Model** は必要に応じて変える
3. ノードを右クリック → **Activate**（有効にする）
4. 「分類」ノードはそのままで AI の答えを使うようになります（表の `classifier` 列が `ai` になる）

OpenAI を使う場合は、「AI分類（Anthropic）」を **OpenAI** ノード（Message a model）に置き換えます。
「分類」ノードは AI の出力の `content`（文字列の配列）を見ているので、OpenAI の出力に合わせて
`const ai = ...` の1行を直してください（例: `$json.output` や `$json.message.content`）。

キーワード判定の言葉を変える・分類を増やすときは、「分類」ノードの `RULES` を書き換えます。

### 通知（Slack）

「チャットに通知」ノード（本体・エラー通知の両方）の **URL** を、Slack の Incoming Webhook の URL に差し替えます。

1. Slack の管理画面で Incoming Webhooks を有効にし、通知したいチャンネルの Webhook URL を発行する
2. 「チャットに通知」ノードの URL 欄を、発行した URL に書き換える
3. 本文は Slack と同じ `{"text": "..."}` 形式で送っているので、そのまま届きます

Webhook URL は秘密の値です。ワークフローを人に渡す前に URL を消すか、ダミーに戻してください。
（Slack ノード ＋ Slack の認証情報を使う形に置き換えることもできます）

### 表（Google スプレッドシート）

「表に記録」ノードを **Google Sheets** ノード（Append row in sheet）に置き換えます。

1. スプレッドシートを作り、1行目に `received_at` `name` `email` `subject` `body` `category` `classifier` を入れる
2. **Credentials** → **Google Sheets OAuth2 API** で、お客様の Google アカウントを接続する
3. 「表に記録」の位置に Google Sheets ノードを置き、Document と Sheet を選び、列を
   `{{ $json.received_at }}` のように「分類」ノードの出力から割り当てる（Mapping Column Mode: Map Each Column Manually）
4. 「受付結果を返す」ノードの `row_id` は Data table の行番号なので、Google Sheets 版では消すか `null` のままでよい

## 3. エラーの確認方法（実行履歴の見方）

- **通知で気づく**: どこかのノードで失敗すると、エラー通知用ワークフローがチャットに
  「ワークフロー名・止まったノード・エラーの内容・実行ID・実行履歴の URL」を送ります
- **どこで止まったかを見る**: ワークフローを開き、画面上部の **Executions** タブを開く。
  失敗した実行は赤い「Error」と表示され、クリックすると止まったノードが赤枠で表示されます。
  そのノードを開くとエラーの内容と、受け取ったデータが見られます
- **直して再実行**: 失敗した実行を開き、**Debug in editor** で同じデータを使って編集画面で試せます

注意:
- エラー通知が飛ぶのは **公開中（Publish 済み）のワークフローが本番で動いたとき** だけです。
  編集画面の「Execute workflow」（テスト実行）での失敗は通知されません
- 実行履歴に残る件数・期間は n8n の設定で決まります（セルフホストは環境変数 `EXECUTIONS_DATA_MAX_AGE` など）

## 4. 動作確認の手順（curl）

```bash
# 1) 通知の受け口を立てる（Slack の代わり。受けた内容を received.jsonl に追記）
python3 tools/dummy_chat_receiver.py 9999 received.jsonl &

# 2) 問い合わせを送る（1件だけ送るとき）
curl -X POST http://127.0.0.1:5678/webhook/inquiry \
  -H 'Content-Type: application/json' \
  -d '{"name":"山田 太郎（ダミー）","email":"taro@example.com","subject":"見積りをお願いします","body":"費用を教えてください"}'
# → {"ok":true,"category":"見積り依頼","classifier":"keyword","row_id":1}

# 3) sample_requests/ をまとめて送る（最後の1件はわざと失敗させる）
./send_samples.sh
```

テスト用の URL（`/webhook-test/inquiry`）は、編集画面で「Execute workflow」を押して待っている間だけ1回受け付けます。
公開後は本番用の `/webhook/inquiry` を使います。

## 実行結果（検証環境・2026-10-10）

`./send_samples.sh` で5件を送った結果です（4件が成功、本文が空の1件がわざとの失敗）。

| ファイル | 内容 |
|---|---|
| `output/curl_responses.txt` | curl の応答。成功4件は分類結果、失敗の1件は HTTP 500 |
| `output/inquiries_table.csv` | Data table「inquiries」に記録された4行 |
| `output/chat_received.jsonl` | 受け口に届いた通知。問い合わせ通知4件 ＋ エラー通知1件 |
| `output/executions.csv` | 実行履歴。本体の成功4件・失敗1件、エラー通知ワークフローの成功1件 |

| 問い合わせ | 分類 |
|---|---|
| 予約システムの見積りをお願いしたいです | 見積り依頼 |
| 管理画面にログインできない | 不具合 |
| 営業時間について | その他 |
| ご相談（料金はいくらくらい？） | 見積り依頼 |
| 本文が空 | エラー → 通知「止まったノード: 入力チェック／必須項目が空です: body」 |

この検証では **AI 分類は呼んでいません**（ノードは無効のまま、キーワード判定で分類）。

## 納品時に先方の環境で気を付けること

- **n8n のバージョン**: このサンプルは n8n 2.42.6 で作りました。Data table ノードは比較的新しい機能なので、
  古い n8n では取り込めない場合があります。その場合は Google スプレッドシート版に置き換えます
- **Node.js**: セルフホストで npm から入れる場合、n8n 2.42.6 は Node.js 24 以上が必要です。
  n8n はコンテナ（Docker）以外での実行を非推奨にしていく方針なので、セルフホストは公式の Docker イメージが無難です
- **公開（Publish）**: 取り込んだだけでは本番用 Webhook は動きません
- **Error workflow の選び直し**: 取り込み後に Settings で選び直します（上の手順4）
- **ファイルを人に渡す前**: n8n の CLI（`n8n export:workflow`）で出した JSON には、アカウント名とメールアドレス
  （`shared` 欄）が入ります。`python3 tools/sanitize_export.py 入力.json 出力.json` で取り除き、「OK」と出ることを確かめます
- **認証情報**: ファイルに入るのは認証情報の名前と ID だけで、パスワードや API キーは入りません。
  接続は取り込んだ先の n8n の画面で行います

## 技術構成

- n8n 2.42.6（Webhook / Code / Anthropic / Data table / HTTP Request / Error Trigger の各ノード）
- 受け口・確認用スクリプトは Python 3.10+ の標準ライブラリのみ
