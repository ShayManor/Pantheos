import json
from app import docker_logs


def test_parse_line_returns_ts_and_stripped_msg():
    rec = {"log": "hello world\n", "stream": "stdout",
           "time": "2026-07-20T04:02:11.123456789Z"}
    out = docker_logs.parse_line(json.dumps(rec))
    assert out["msg"] == "hello world"
    assert abs(out["ts"] - 1784520131.123456) < 1e-3


def test_parse_line_keeps_interior_whitespace():
    rec = {"log": "  a  b\n", "stream": "stderr", "time": "2026-07-20T04:02:11Z"}
    assert docker_logs.parse_line(json.dumps(rec))["msg"] == "  a  b"


def test_parse_line_bad_json_returns_none():
    assert docker_logs.parse_line("not json") is None


def test_parse_line_missing_keys_returns_none():
    assert docker_logs.parse_line(json.dumps({"log": "x"})) is None


def test_parse_line_bad_time_returns_none():
    rec = {"log": "x\n", "stream": "stdout", "time": "not-a-time"}
    assert docker_logs.parse_line(json.dumps(rec)) is None


def test_level_err_on_error_markers():
    for m in ["[ERROR] boom", "CRITICAL: down", "FATAL: x", "Traceback (most recent call last):"]:
        assert docker_logs.level(m) == "err"


def test_level_warn_on_warning_markers():
    for m in ["[WARNING] slow", "WARN retrying"]:
        assert docker_logs.level(m) == "warn"


def test_level_info_default():
    assert docker_logs.level("[INFO] Booting worker with pid: 8") == "info"


def test_name_from_config_strips_leading_slash():
    cfg = json.dumps({"Name": "/pantheos-mcp-1"})
    assert docker_logs.name_from_config(cfg) == "pantheos-mcp-1"


def test_name_from_config_bad_or_missing_returns_none():
    assert docker_logs.name_from_config("not json") is None
    assert docker_logs.name_from_config(json.dumps({})) is None
