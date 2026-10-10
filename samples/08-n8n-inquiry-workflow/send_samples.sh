#!/bin/bash
# sample_requests/ の問い合わせを Webhook に順に送る。
# 使い方: ./send_samples.sh [Webhook の URL]（既定: http://127.0.0.1:5678/webhook/inquiry）
URL="${1:-http://127.0.0.1:5678/webhook/inquiry}"
cd "$(dirname "$0")"
for f in sample_requests/*.json; do
  echo "== $f"
  curl -s -w '\n(HTTP %{http_code})\n' -X POST "$URL" -H 'Content-Type: application/json' --data-binary "@$f"
done
