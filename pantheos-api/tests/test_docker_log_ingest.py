import json
from app import docker_log_ingest
from app.models import IngestState, LogLine


def _rec(msg, t="2026-07-20T04:02:11.000000000Z"):
    return {"log": msg + "\n", "stream": "stdout", "time": t}


def _write(p, recs):
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n")


def _container_dir(root, chash, name):
    """Fake a Docker container dir: config.v2.json + the <hash>-json.log path."""
    d = root / "containers" / chash
    d.mkdir(parents=True)
    (d / "config.v2.json").write_text(json.dumps({"Name": "/" + name}))
    return d / f"{chash}-json.log"


# ---------------------------------------------------------------- ingest_once

def test_ingest_appends_docker_rows_with_levels(session, tmp_path):
    p = tmp_path / "c-json.log"
    _write(p, [_rec("[INFO] booting"), _rec("[ERROR] boom")])
    n = docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    assert n == 2
    rows = session.query(LogLine).filter_by(container_id="pantheos-mcp-1", source="docker").all()
    assert {r.lvl for r in rows} == {"info", "err"}
    assert all(r.source == "docker" for r in rows)


def test_ingest_advances_offset_no_dupes(session, tmp_path):
    p = tmp_path / "c-json.log"
    _write(p, [_rec("a")])
    docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    p.write_text(p.read_text() + json.dumps(_rec("b")) + "\n")
    docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    assert session.query(LogLine).filter_by(container_id="pantheos-mcp-1", source="docker").count() == 2


def test_ingest_handles_rotation(session, tmp_path):
    p = tmp_path / "c-json.log"
    _write(p, [_rec("a")])
    docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    st = session.get(IngestState, str(p)); st.inode += 999999; session.commit()
    _write(p, [_rec("rotated")])
    docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    assert session.query(LogLine).filter(LogLine.msg.contains("rotated")).count() == 1


def test_ingest_handles_truncation(session, tmp_path):
    p = tmp_path / "c-json.log"
    _write(p, [_rec("a"), _rec("b"), _rec("c")])
    docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    _write(p, [_rec("short")])
    n = docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1")
    assert n == 1
    assert session.query(LogLine).filter(LogLine.msg.contains("short")).count() == 1


def test_ingest_holds_partial_trailing_line(session, tmp_path):
    p = tmp_path / "c-json.log"
    p.write_text(json.dumps(_rec("a")) + '\n{"log":"partial')  # no newline
    assert docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1") == 1


def test_ingest_missing_file_returns_zero(session, tmp_path):
    assert docker_log_ingest.ingest_once(session, str(tmp_path / "nope.log"), "pantheos-mcp-1") == 0


def test_ingest_skips_unparseable_lines(session, tmp_path):
    p = tmp_path / "c-json.log"; p.write_text("not json\n")
    assert docker_log_ingest.ingest_once(session, str(p), "pantheos-mcp-1") == 0


# ---------------------------------------------------------------- targets

def test_container_targets_filters_to_inventory(tmp_path):
    good = _container_dir(tmp_path, "aaa", "pantheos-mcp-1")
    good.write_text("")                                   # log file present
    other = _container_dir(tmp_path, "bbb", "some-random-container")
    other.write_text("")
    targets = docker_log_ingest.container_targets(str(tmp_path))
    assert targets == [("pantheos-mcp-1", str(good))]


def test_container_targets_skips_dir_without_log_file(tmp_path):
    _container_dir(tmp_path, "ccc", "pantheos-mcp-1")     # config but no *-json.log
    assert docker_log_ingest.container_targets(str(tmp_path)) == []


def test_container_targets_missing_root_returns_empty(tmp_path):
    assert docker_log_ingest.container_targets(str(tmp_path / "nope")) == []


def test_container_targets_skips_dir_without_config(tmp_path):
    (tmp_path / "containers" / "eee").mkdir(parents=True)   # no config.v2.json
    assert docker_log_ingest.container_targets(str(tmp_path)) == []


# ---------------------------------------------------------------- run_once

def test_run_once_ingests_targets_and_prunes(session, tmp_path, monkeypatch):
    log = _container_dir(tmp_path, "ddd", "pantheos-mcp-1")
    _write(log, [_rec("[INFO] hi")])
    pruned = []
    monkeypatch.setattr(docker_log_ingest.logview, "prune",
                        lambda s, cid, now: pruned.append(cid))
    n = docker_log_ingest.run_once(session, str(tmp_path), now=1e9)
    assert n == 1
    assert pruned == ["pantheos-mcp-1"]
    assert session.query(LogLine).filter_by(container_id="pantheos-mcp-1", source="docker").count() == 1
