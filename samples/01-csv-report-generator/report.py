"""CSV売上データから集計済みHTMLレポートを生成するツール.

使い方:
    python report.py --input sample_data/sales_2026q1.csv --output output/report.html
    python report.py  # 引数なしならサンプルで実行

入力CSVの列: date, product, category, quantity, unit_price
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path


@dataclass
class Row:
    date: str
    product: str
    category: str
    quantity: int
    unit_price: int

    @property
    def revenue(self) -> int:
        return self.quantity * self.unit_price

    @property
    def month(self) -> str:
        return self.date[:7]


def load_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    skipped = 0
    required = {"date", "product", "category", "quantity", "unit_price"}
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(
                f"CSVに必要な列がありません: {sorted(missing)}. 期待: {sorted(required)}"
            )
        for line_no, raw in enumerate(reader, start=2):
            try:
                rows.append(
                    Row(
                        date=raw["date"].strip(),
                        product=raw["product"].strip(),
                        category=raw["category"].strip(),
                        quantity=int(raw["quantity"]),
                        unit_price=int(raw["unit_price"]),
                    )
                )
            except (ValueError, AttributeError, KeyError) as e:
                skipped += 1
                print(f"[WARN] {path.name}:{line_no} を読み飛ばし: {e}", file=__import__('sys').stderr)
    if skipped:
        print(f"[INFO] {skipped}行を読み飛ばしました（型不正・欠損）", file=__import__('sys').stderr)
    rows.sort(key=lambda r: r.date)
    return rows


def aggregate(rows: list[Row]) -> dict:
    if not rows:
        return {"empty": True}

    total_revenue = sum(r.revenue for r in rows)
    total_qty = sum(r.quantity for r in rows)
    avg_unit = total_revenue / total_qty if total_qty else 0

    monthly: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    by_product: dict[str, dict] = defaultdict(lambda: {"revenue": 0, "qty": 0})

    for r in rows:
        monthly[r.month] += r.revenue
        by_category[r.category] += r.revenue
        by_product[r.product]["revenue"] += r.revenue
        by_product[r.product]["qty"] += r.quantity

    months = sorted(monthly.keys())
    monthly_series = [{"label": m, "value": monthly[m]} for m in months]
    category_series = sorted(
        ({"label": k, "value": v} for k, v in by_category.items()),
        key=lambda x: x["value"],
        reverse=True,
    )
    product_top10 = sorted(
        (
            {"label": p, "revenue": d["revenue"], "qty": d["qty"]}
            for p, d in by_product.items()
        ),
        key=lambda x: x["revenue"],
        reverse=True,
    )[:10]

    return {
        "empty": False,
        "kpi": {
            "total_revenue": total_revenue,
            "total_count": len(rows),
            "avg_unit_price": round(avg_unit),
            "last_date": rows[-1].date,
            "first_date": rows[0].date,
        },
        "monthly": monthly_series,
        "category": category_series,
        "product_top10": product_top10,
        "rows": [
            {
                "date": r.date,
                "product": r.product,
                "category": r.category,
                "quantity": r.quantity,
                "unit_price": r.unit_price,
                "revenue": r.revenue,
            }
            for r in rows
        ],
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>売上レポート ({first} 〜 {last})</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #f5f7fa;
    --card: #ffffff;
    --ink: #1f2937;
    --muted: #6b7280;
    --accent: #2563eb;
    --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 32px 24px;
    background: var(--bg); color: var(--ink);
    font-family: -apple-system, "Hiragino Sans", "Meiryo", system-ui, sans-serif;
  }}
  h1 {{ margin: 0 0 8px; font-size: 24px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 24px; font-size: 14px; }}
  .kpi {{
    display: grid; gap: 16px; margin-bottom: 24px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }}
  .kpi .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px;
  }}
  .kpi .label {{ color: var(--muted); font-size: 12px; }}
  .kpi .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
  .grid {{
    display: grid; gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  }}
  .panel {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px;
  }}
  .panel h2 {{ margin: 0 0 12px; font-size: 16px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px; border-bottom: 1px solid var(--border); text-align: left; }}
  th {{ background: #f9fafb; font-weight: 600; }}
  td.num, th.num {{ text-align: right; }}
  .filter {{ margin-bottom: 8px; }}
  .filter input {{
    width: 240px; padding: 6px 8px;
    border: 1px solid var(--border); border-radius: 6px;
  }}
  footer {{
    margin-top: 32px; color: var(--muted);
    font-size: 12px; text-align: center;
  }}
  canvas {{ max-height: 280px; }}
</style>
</head>
<body>
  <h1>売上レポート</h1>
  <p class="subtitle">期間: {first} 〜 {last} / 生成日時: {generated_at}</p>

  <section class="kpi">
    <div class="card"><div class="label">総売上</div><div class="value">¥{total_revenue:,}</div></div>
    <div class="card"><div class="label">取引件数</div><div class="value">{total_count:,}</div></div>
    <div class="card"><div class="label">平均単価</div><div class="value">¥{avg_unit_price:,}</div></div>
    <div class="card"><div class="label">最終取引日</div><div class="value">{last}</div></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h2>月次売上推移</h2>
      <canvas id="monthly"></canvas>
    </div>
    <div class="panel">
      <h2>カテゴリ別売上</h2>
      <canvas id="category"></canvas>
    </div>
    <div class="panel" style="grid-column: 1 / -1;">
      <h2>商品別売上 TOP10</h2>
      <canvas id="topproducts"></canvas>
    </div>
  </section>

  <section class="panel" style="margin-top: 16px;">
    <h2>明細</h2>
    <div class="filter">
      <input id="search" placeholder="商品名・カテゴリで絞り込み">
    </div>
    <table id="rows">
      <thead>
        <tr><th>日付</th><th>商品</th><th>カテゴリ</th><th class="num">数量</th><th class="num">単価</th><th class="num">売上</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </section>

  <footer>Generated by ai-automation-samples / sample 01-csv-report-generator</footer>

<script>
const DATA = {data_json};

const monthly = DATA.monthly;
const category = DATA.category;
const top = DATA.product_top10;

new Chart(document.getElementById('monthly'), {{
  type: 'line',
  data: {{
    labels: monthly.map(m => m.label),
    datasets: [{{
      label: '売上',
      data: monthly.map(m => m.value),
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, 0.15)',
      fill: true, tension: 0.3,
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

new Chart(document.getElementById('category'), {{
  type: 'doughnut',
  data: {{
    labels: category.map(c => c.label),
    datasets: [{{
      data: category.map(c => c.value),
      backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16'],
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false }}
}});

new Chart(document.getElementById('topproducts'), {{
  type: 'bar',
  data: {{
    labels: top.map(t => t.label),
    datasets: [{{
      label: '売上',
      data: top.map(t => t.revenue),
      backgroundColor: '#10b981',
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true, maintainAspectRatio: false,
  }}
}});

const tbody = document.querySelector('#rows tbody');
function render(filter) {{
  tbody.innerHTML = '';
  const f = (filter || '').toLowerCase();
  for (const r of DATA.rows) {{
    if (f && !(r.product.toLowerCase().includes(f) || r.category.toLowerCase().includes(f))) continue;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{r.date}}</td><td>${{r.product}}</td><td>${{r.category}}</td>` +
                   `<td class="num">${{r.quantity}}</td>` +
                   `<td class="num">¥${{r.unit_price.toLocaleString()}}</td>` +
                   `<td class="num">¥${{r.revenue.toLocaleString()}}</td>`;
    tbody.appendChild(tr);
  }}
}}
render('');
document.getElementById('search').addEventListener('input', (e) => render(e.target.value));
</script>
</body>
</html>
"""


def render_html(agg: dict) -> str:
    if agg.get("empty"):
        return "<html><body><p>データがありません</p></body></html>"
    kpi = agg["kpi"]
    return HTML_TEMPLATE.format(
        first=escape(kpi["first_date"]),
        last=escape(kpi["last_date"]),
        total_revenue=kpi["total_revenue"],
        total_count=kpi["total_count"],
        avg_unit_price=kpi["avg_unit_price"],
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        data_json=json.dumps(agg, ensure_ascii=False),
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", default=str(here / "sample_data" / "sales_2026q1.csv")
    )
    parser.add_argument(
        "--output", default=str(here / "output" / "sample_report.html")
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = load_rows(in_path)
    agg = aggregate(rows)
    html = render_html(agg)
    out_path.write_text(html, encoding="utf-8")

    if not agg.get("empty"):
        kpi = agg["kpi"]
        print(f"[OK] {len(rows)} 件を集計 → {out_path}")
        print(f"     期間: {kpi['first_date']} 〜 {kpi['last_date']}")
        print(f"     総売上: ¥{kpi['total_revenue']:,}")
        print(f"     取引数: {kpi['total_count']:,} / 平均単価: ¥{kpi['avg_unit_price']:,}")
        if agg.get("category"):
            top_cat = agg["category"][0]
            print(f"     主力カテゴリ: {top_cat['label']} (¥{top_cat['value']:,})")
        if agg.get("product_top10"):
            top_prod = agg["product_top10"][0]
            print(f"     売れ筋: {top_prod['label']} (¥{top_prod['revenue']:,})")
    else:
        print("[WARN] 集計対象データがありません。CSVの内容をご確認ください。")


if __name__ == "__main__":
    main()
