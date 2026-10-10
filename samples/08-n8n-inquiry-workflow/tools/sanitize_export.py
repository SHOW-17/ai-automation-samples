"""n8n からエクスポートしたワークフロー JSON を、人に渡せる形に整える。

- アカウント情報（shared: プロジェクト名にメールアドレスが入る）、インスタンスID（meta）、
  日時・バージョン・公開状態など、渡し先で不要な欄を消す
- 認証情報（credentials）は名前とIDだけが入るので、ノードから外す（渡し先で選び直す）
- 消したあとに、メールアドレス・認証ヘッダ・鍵らしい文字列が残っていないかを確かめ、
  見つかったら終了コード 1 で知らせる

使い方: python3 sanitize_export.py 入力.json 出力.json
"""
import json
import re
import sys

KEEP = ["name", "nodes", "connections", "settings", "id"]
SUSPICIOUS = [
    (re.compile(r"[\w.+-]+@(?!example\.(com|org|net)\b)[\w-]+\.[\w.]+"), "メールアドレス（example.com 以外）"),
    (re.compile(r"(?i)\b(authorization|x-api-key|bearer)\b"), "認証ヘッダ"),
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|xox[abp]-[A-Za-z0-9-]+)"), "APIキー・トークン"),
    (re.compile(r"hooks\.slack\.com/services/[A-Z0-9]+/[A-Z0-9]+/[A-Za-z0-9]+"), "Slack Webhook URL"),
]


def sanitize(wf: dict) -> dict:
    out = {k: wf[k] for k in KEEP if k in wf}
    for node in out["nodes"]:
        node.pop("credentials", None)
    return out


def find_suspicious(text: str) -> list[str]:
    return [f"{label}: {m.group(0)}" for pat, label in SUSPICIOUS for m in pat.finditer(text)]


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        wf = json.load(f)
    text = json.dumps(sanitize(wf), ensure_ascii=False, indent=2) + "\n"
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    hits = find_suspicious(text)
    for h in hits:
        print(f"要確認 {h}", file=sys.stderr)
    print(f"{dst}: {'要確認あり' if hits else 'OK'}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
