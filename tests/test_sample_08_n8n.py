"""Sample 08: n8n ワークフロー JSON の形と、エクスポートの後始末スクリプトのテスト"""
import json
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "08-n8n-inquiry-workflow"
sys.path.insert(0, str(SAMPLE / "tools"))

import sanitize_export  # noqa: E402

WORKFLOWS = sorted((SAMPLE / "workflows").glob("*.json"))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_two_workflows_exist():
    assert {p.name for p in WORKFLOWS} == {"inquiry-workflow.json", "error-notify-workflow.json"}


def test_connections_point_to_existing_nodes():
    for path in WORKFLOWS:
        wf = load(path)
        names = {n["name"] for n in wf["nodes"]}
        assert len(names) == len(wf["nodes"]), f"{path.name}: ノード名が重複"
        for src, outs in wf["connections"].items():
            assert src in names
            for branch in outs["main"]:
                for c in branch:
                    assert c["node"] in names


def test_no_credentials_or_account_info():
    for path in WORKFLOWS:
        wf = load(path)
        assert set(wf) <= set(sanitize_export.KEEP), f"{path.name}: 余計な欄 {set(wf) - set(sanitize_export.KEEP)}"
        assert all("credentials" not in n for n in wf["nodes"])
        assert sanitize_export.find_suspicious(path.read_text(encoding="utf-8")) == []


def test_main_workflow_shape():
    wf = load(SAMPLE / "workflows" / "inquiry-workflow.json")
    types = [n["type"] for n in wf["nodes"]]
    assert types[0] == "n8n-nodes-base.webhook"
    assert "n8n-nodes-base.dataTable" in types
    ai = next(n for n in wf["nodes"] if n["type"] == "@n8n/n8n-nodes-langchain.anthropic")
    assert ai.get("disabled") is True, "AI ノードは初期状態で無効（APIキー不要で動かすため）"
    assert wf["settings"]["errorWorkflow"] == load(SAMPLE / "workflows" / "error-notify-workflow.json")["id"]


def test_error_workflow_starts_with_error_trigger():
    wf = load(SAMPLE / "workflows" / "error-notify-workflow.json")
    assert wf["nodes"][0]["type"] == "n8n-nodes-base.errorTrigger"


def test_sanitize_removes_account_and_credentials(tmp_path):
    raw = {
        "name": "x", "id": "abc", "connections": {}, "settings": {},
        "nodes": [{"name": "n", "type": "t", "credentials": {"anthropicApi": {"id": "1", "name": "my key"}}}],
        "shared": [{"project": {"name": "Someone <someone@company.co.jp>"}}],
        "meta": {"instanceId": "deadbeef"}, "versionId": "v1", "active": True,
    }
    src, dst = tmp_path / "in.json", tmp_path / "out.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    sys.argv = ["sanitize_export.py", str(src), str(dst)]
    assert sanitize_export.main() == 0
    out = json.loads(dst.read_text(encoding="utf-8"))
    assert set(out) == {"name", "id", "connections", "settings", "nodes"}
    assert "credentials" not in out["nodes"][0]


def test_find_suspicious_detects_secrets():
    hits = sanitize_export.find_suspicious(
        '{"url": "https://hooks.slack.com/services/T000/B000/abcdef123", "h": "Authorization", "m": "a@company.co.jp"}'
    )
    assert len(hits) == 3
    assert sanitize_export.find_suspicious('{"email": "taro@example.com"}') == []
