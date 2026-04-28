"""複数サイトの価格を定期監視し、変動アラートとHTMLレポートを生成する.

使い方:
    python monitor.py                  # watchlist.csv で実運用
    python monitor.py --demo           # ローカルサンプルでE2Eデモ

監視先のURLが http(s):// で始まれば実スクレイプ、file:// やローカルパスならファイル読み込み.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_WATCHLIST = HERE / "sample_data" / "watchlist.csv"
HISTORY_PATH = HERE / "output" / "history.csv"
ALERTS_PATH = HERE / "output" / "alerts.csv"
REPORT_PATH = HERE / "output" / "report.html"


@dataclass
class WatchTarget:
    name: str
    url: str
    css_selector: str
    threshold_pct: float

    def resolved_url(self) -> str:
        if self.url.startswith(("http://", "https://", "file://")):
            return self.url
        # ローカル相対パスを sample_data 基準で解決
        path = (HERE / "sample_data" / self.url).resolve()
        return path.as_uri()


def load_watchlist(path: Path) -> list[WatchTarget]:
    targets: list[WatchTarget] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            targets.append(
                WatchTarget(
                    name=row["name"].strip(),
                    url=row["url"].strip(),
                    css_selector=row["css_selector"].strip(),
                    threshold_pct=float(row.get("threshold_pct", "5")),
                )
            )
    return targets


# --------------- 取得とパース ---------------


def fetch(url: str, ua: str = "PriceMonitor/1.0 (contact@example.com)") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_with_bs(html: str, selector: str) -> str | None:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        return _extract_naive(html, selector)
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


def _extract_naive(html: str, selector: str) -> str | None:
    """BeautifulSoup未インストール環境向けの素朴な抽出（class/idのみ対応）."""
    import re

    if selector.startswith("."):
        cls = selector[1:].split(" ")[0].split(",")[0]
        m = re.search(rf'class="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*>([^<]+)<', html)
    elif selector.startswith("#"):
        i = selector[1:]
        m = re.search(rf'id="{re.escape(i)}"[^>]*>([^<]+)<', html)
    else:
        m = re.search(rf"<{selector}[^>]*>([^<]+)</{selector}>", html)
    return m.group(1).strip() if m else None


def parse_price(text: str) -> int | None:
    if not text:
        return None
    digits = "".join(c for c in text if c.isdigit())
    return int(digits) if digits else None


# --------------- 履歴管理 ---------------


def append_history(records: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not HISTORY_PATH.exists()
    with HISTORY_PATH.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "name", "url", "price", "raw_text"])
        if is_new:
            w.writeheader()
        for r in records:
            w.writerow(r)


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def previous_price(history: list[dict], name: str, current_ts: str) -> int | None:
    for row in reversed(history):
        if row["name"] == name and row["timestamp"] != current_ts and row["price"]:
            return int(row["price"])
    return None


# --------------- アラート判定 ---------------


def detect_alerts(
    targets: list[WatchTarget],
    current: dict[str, int | None],
    prev: dict[str, int | None],
) -> list[dict]:
    alerts: list[dict] = []
    for t in targets:
        cur = current.get(t.name)
        pv = prev.get(t.name)
        if cur is None or pv is None or pv == 0:
            continue
        diff_pct = (cur - pv) / pv * 100
        if abs(diff_pct) >= t.threshold_pct:
            alerts.append(
                {
                    "name": t.name,
                    "url": t.url,
                    "previous": pv,
                    "current": cur,
                    "diff_pct": round(diff_pct, 2),
                    "direction": "up" if diff_pct > 0 else "down",
                }
            )
    return alerts


def write_alerts(alerts: list[dict]) -> None:
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["timestamp", "name", "url", "previous", "current", "diff_pct", "direction"]
        )
        w.writeheader()
        ts = datetime.now().isoformat(timespec="seconds")
        for a in alerts:
            w.writerow({"timestamp": ts, **a})


# --------------- HTMLレポート ---------------


def render_report(targets: list[WatchTarget], history: list[dict], alerts: list[dict]) -> str:
    series_by_name: dict[str, list[dict]] = {t.name: [] for t in targets}
    for row in history:
        if row["name"] in series_by_name and row["price"]:
            series_by_name[row["name"]].append(
                {"t": row["timestamp"][:10], "v": int(row["price"])}
            )
    chart_data = json.dumps(series_by_name, ensure_ascii=False)

    alert_rows = "".join(
        f'<tr class="alert-{a["direction"]}">'
        f'<td>{escape(a["name"])}</td>'
        f"<td>¥{a['previous']:,}</td><td>¥{a['current']:,}</td>"
        f'<td>{a["diff_pct"]:+.2f}%</td>'
        f'<td><a href="{escape(a["url"])}" target="_blank">詳細</a></td></tr>'
        for a in alerts
    )

    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<title>価格モニタリングレポート</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
body {{ font-family: -apple-system, "Hiragino Sans", system-ui, sans-serif; max-width: 960px; margin: 24px auto; padding: 0 16px; color: #1f2937; background: #f5f7fa; }}
h1 {{ font-size: 22px; }}
.card {{ background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th, td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: left; }}
th {{ background: #f9fafb; }}
tr.alert-up td:nth-child(4) {{ color: #dc2626; font-weight: 600; }}
tr.alert-down td:nth-child(4) {{ color: #16a34a; font-weight: 600; }}
.empty {{ color: #6b7280; font-style: italic; }}
canvas {{ max-height: 320px; }}
</style></head><body>
<h1>📈 価格モニタリングレポート</h1>
<p>生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M")} / 監視対象: {len(targets)}件</p>

<div class="card">
  <h2 style="margin-top:0">⚠️ 直近のアラート</h2>
  {f'<table><thead><tr><th>商品</th><th>前回</th><th>今回</th><th>変動</th><th></th></tr></thead><tbody>{alert_rows}</tbody></table>' if alert_rows else '<p class="empty">閾値超えの変動はありません</p>'}
</div>

<div class="card">
  <h2 style="margin-top:0">価格推移</h2>
  <canvas id="chart"></canvas>
</div>

<script>
const data = {chart_data};
const colors = ['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899'];
const allLabels = new Set();
Object.values(data).forEach(arr => arr.forEach(p => allLabels.add(p.t)));
const labels = [...allLabels].sort();
const datasets = Object.entries(data).map(([name, arr], i) => {{
  const map = Object.fromEntries(arr.map(p => [p.t, p.v]));
  return {{
    label: name, data: labels.map(l => map[l] ?? null),
    borderColor: colors[i % colors.length], spanGaps: true, tension: 0.3,
  }};
}});
new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{ labels, datasets }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});
</script>
</body></html>"""


# --------------- メインフロー ---------------


def run_monitoring(watchlist_path: Path, request_delay: float = 1.0) -> None:
    targets = load_watchlist(watchlist_path)
    print(f"[INFO] {len(targets)}件を監視", file=sys.stderr)

    history = load_history()
    ts = datetime.now().isoformat(timespec="seconds")

    current: dict[str, int | None] = {}
    new_records: list[dict] = []

    for t in targets:
        url = t.resolved_url()
        try:
            html = fetch(url)
            text = extract_with_bs(html, t.css_selector)
            price = parse_price(text or "")
            current[t.name] = price
            new_records.append(
                {
                    "timestamp": ts,
                    "name": t.name,
                    "url": t.url,
                    "price": price if price is not None else "",
                    "raw_text": (text or "")[:60],
                }
            )
            print(f"  [OK] {t.name}: ¥{price:,}" if price else f"  [WARN] {t.name}: 価格抽出失敗")
        except Exception as e:
            print(f"  [ERR] {t.name}: {e}", file=sys.stderr)
            current[t.name] = None
        time.sleep(request_delay)

    append_history(new_records)
    history = load_history()

    prev: dict[str, int | None] = {t.name: previous_price(history, t.name, ts) for t in targets}
    alerts = detect_alerts(targets, current, prev)
    write_alerts(alerts)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(targets, history, alerts), encoding="utf-8")

    print(f"[OK] {len(alerts)}件のアラート / レポート: {REPORT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST))
    parser.add_argument("--demo", action="store_true", help="サンプル履歴を流し込んでE2Eデモ")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    if args.demo:
        seed_demo_history()

    run_monitoring(Path(args.watchlist), request_delay=args.delay)


def seed_demo_history() -> None:
    """過去30日分のダミー履歴を history.csv に書き込む（デモ用初期化）."""
    src = HERE / "sample_data" / "history_30days.csv"
    if not src.exists():
        return
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[INFO] デモ用履歴をシード: {HISTORY_PATH}")


if __name__ == "__main__":
    main()
