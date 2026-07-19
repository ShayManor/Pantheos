import json
from app import log_ingest
from app.models import IngestState, LogLine


def _write(p, records):
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def _rec(host, status, uri):
    return {"ts": 1e9, "duration": 0.01, "status": status,
            "request": {"method": "GET", "host": host, "uri": uri}}


def test_ingest_routes_by_host_and_levels(session, tmp_path):
    p = tmp_path / "access.log"
    _write(p, [_rec("pantheos.app", 200, "/a"), _rec("pantheos.app", 500, "/b"),
               _rec("nobody.example", 200, "/c")])          # unroutable host skipped
    n = log_ingest.ingest_once(session, str(p))
    assert n == 2
    rows = session.query(LogLine).filter_by(container_id="pantheos-app-1", source="caddy").all()
    assert {r.lvl for r in rows} == {"info", "err"}


def test_ingest_advances_offset_no_dupes(session, tmp_path):
    p = tmp_path / "access.log"
    _write(p, [_rec("pantheos.app", 200, "/a")])
    log_ingest.ingest_once(session, str(p))
    p.write_text(p.read_text() + json.dumps(_rec("pantheos.app", 200, "/b")) + "\n")
    log_ingest.ingest_once(session, str(p))
    rows = session.query(LogLine).filter_by(container_id="pantheos-app-1", source="caddy").all()
    assert len(rows) == 2                                   # each line ingested once


def test_ingest_handles_rotation(session, tmp_path):
    p = tmp_path / "access.log"
    _write(p, [_rec("pantheos.app", 200, "/a")])
    log_ingest.ingest_once(session, str(p))
    st = session.get(IngestState, str(p)); st.inode = st.inode + 999999; session.commit()
    _write(p, [_rec("pantheos.app", 200, "/rotated")])      # inode mismatch → read from 0
    log_ingest.ingest_once(session, str(p))
    assert session.query(LogLine).filter(LogLine.msg.contains("/rotated")).count() == 1


def test_ingest_holds_partial_trailing_line(session, tmp_path):
    p = tmp_path / "access.log"
    p.write_text(json.dumps(_rec("pantheos.app", 200, "/a")) + "\n{\"partial\":")  # no newline
    n = log_ingest.ingest_once(session, str(p))
    assert n == 1                                           # partial not consumed
    p.write_text(json.dumps(_rec("pantheos.app", 200, "/a")) + "\n"
                 + json.dumps(_rec("pantheos.app", 200, "/b")) + "\n")
    log_ingest.ingest_once(session, str(p))
    assert session.query(LogLine).filter(LogLine.msg.contains("/b")).count() == 1


def test_ingest_handles_truncation(session, tmp_path):
    p = tmp_path / "access.log"
    _write(p, [_rec("pantheos.app", 200, "/a"), _rec("pantheos.app", 200, "/b"),
               _rec("pantheos.app", 200, "/c")])
    log_ingest.ingest_once(session, str(p))
    _write(p, [_rec("pantheos.app", 200, "/short")])        # truncated in place, same inode
    n = log_ingest.ingest_once(session, str(p))
    assert n == 1
    assert session.query(LogLine).filter(LogLine.msg.contains("/short")).count() == 1


def test_ingest_missing_file_returns_zero(session, tmp_path):
    assert log_ingest.ingest_once(session, str(tmp_path / "nope.log")) == 0


def test_ingest_skips_bad_json(session, tmp_path):
    p = tmp_path / "access.log"; p.write_text("not json\n")
    assert log_ingest.ingest_once(session, str(p)) == 0


def test_run_once_prunes(session, tmp_path, monkeypatch):
    calls = {}
    monkeypatch.setattr(log_ingest, "prune_all", lambda s, now: calls.setdefault("now", now))
    p = tmp_path / "access.log"; _write(p, [_rec("pantheos.app", 200, "/a")])
    log_ingest.run_once(session, str(p), now=123.0)
    assert calls["now"] == 123.0


def test_prune_all_runs_over_caddy_containers(session, tmp_path):
    p = tmp_path / "access.log"; _write(p, [_rec("pantheos.app", 200, "/a")])
    log_ingest.ingest_once(session, str(p))
    log_ingest.prune_all(session, now=1e9 + 1)              # should not raise
