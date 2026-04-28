"""sample 01 (CSV売上レポート) のユニットテスト."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "01-csv-report-generator"
sys.path.insert(0, str(SAMPLE))

import report  # type: ignore


def make_csv(tmp_path: Path, rows: list[list]) -> Path:
    p = tmp_path / "sales.csv"
    lines = ["date,product,category,quantity,unit_price"]
    lines.extend(",".join(str(c) for c in row) for row in rows)
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def test_load_rows_basic(tmp_path):
    csv_path = make_csv(
        tmp_path,
        [
            ["2026-01-01", "カフェラテ", "ドリンク", 2, 480],
            ["2026-01-02", "クッキー", "フード", 1, 280],
        ],
    )
    rows = report.load_rows(csv_path)
    assert len(rows) == 2
    assert rows[0].revenue == 960
    assert rows[1].month == "2026-01"


def test_load_rows_skips_invalid(tmp_path, capsys):
    csv_path = make_csv(
        tmp_path,
        [
            ["2026-01-01", "カフェラテ", "ドリンク", 2, 480],
            ["broken", "row", "row", "not_a_number", "abc"],
            ["2026-01-02", "クッキー", "フード", 1, 280],
        ],
    )
    rows = report.load_rows(csv_path)
    assert len(rows) == 2
    err = capsys.readouterr().err
    assert "読み飛ばし" in err


def test_load_rows_missing_columns(tmp_path):
    p = tmp_path / "broken.csv"
    p.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="必要な列"):
        report.load_rows(p)


def test_aggregate_kpi(tmp_path):
    csv_path = make_csv(
        tmp_path,
        [
            ["2026-01-01", "カフェラテ", "ドリンク", 2, 480],
            ["2026-01-01", "クッキー", "フード", 1, 280],
            ["2026-02-01", "カフェラテ", "ドリンク", 1, 480],
        ],
    )
    rows = report.load_rows(csv_path)
    agg = report.aggregate(rows)
    kpi = agg["kpi"]
    assert kpi["total_revenue"] == 960 + 280 + 480
    assert kpi["total_count"] == 3
    assert kpi["first_date"] == "2026-01-01"
    assert kpi["last_date"] == "2026-02-01"


def test_aggregate_empty():
    agg = report.aggregate([])
    assert agg["empty"] is True


def test_render_html_contains_title(tmp_path):
    csv_path = make_csv(tmp_path, [["2026-01-01", "X", "Y", 1, 100]])
    rows = report.load_rows(csv_path)
    html = report.render_html(report.aggregate(rows))
    assert "売上レポート" in html
    assert "Chart" in html
