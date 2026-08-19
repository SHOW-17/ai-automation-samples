# CLAUDE.md — ai-automation-samples

ココナラで提供している5つのサービスの実物サンプル成果物集。GitHub **公開リポジトリ**（営業材料として発注前の顧客に見せる）。

## 公開リポジトリとしての注意

- **非公開情報を書かない**: 顧客名・単価交渉の経緯・見積もり内訳・受注状況などは書かない。案件記録の正本は HQ（`/home/ubuntu/apps/side-business-hq`）にあり、そちらにのみ記録する
- サンプルは「実際にこういうものが届きます」を見せるためのものなので、実データ・実顧客の情報を混ぜない（モック/サンプルデータのみ）

## 変更時のルール

- 内容を変更したら **`README.md` と `README.en.md` の両方を更新する**（日英で内容を揃える）
- 検証は CI と同じ手順で行う（`.github/workflows/ci.yml` 参照）:
  ```bash
  pip install openpyxl beautifulsoup4 pytest
  python -m pytest tests/ -v
  ```
  CI はこれに加えて各 `samples/*/` 配下のサンプルスクリプトをモック/デモモードで実行して疎通確認している。大きめの変更をした場合は該当サンプルのスクリプトも手元で実行して確認する
