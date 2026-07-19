from app.models import IngestState, LogLine


def test_logline_roundtrip(session):
    session.query(LogLine).filter_by(container_id="ghstats-edge").delete()  # clear seeded mock rows
    session.add(LogLine(container_id="ghstats-edge", source="mock",
                        ts=1_700_000_000.0, lvl="err", msg="boom"))
    session.commit()
    row = session.query(LogLine).filter_by(container_id="ghstats-edge").one()
    assert row.lvl == "err" and row.source == "mock" and isinstance(row.id, int)


def test_ingest_state_roundtrip(session):
    session.add(IngestState(path="/tmp/a.log", inode=42, offset=100))
    session.commit()
    assert session.get(IngestState, "/tmp/a.log").offset == 100


from collections import namedtuple
from app import logview

Row = namedtuple("Row", "id ts lvl msg")


def _rows(spec):
    # spec: list of (id, lvl) newest-first; ts = id for simplicity
    return [Row(i, float(i), lvl, f"m{i}") for i, lvl in spec]


def test_collapse_gaps_long_info_runs():
    rows = _rows([(i, "info") for i in range(30, 0, -1)])  # 30 info, no errors
    items = logview.collapse(rows, ctx=5)
    assert len(items) == 1 and items[0]["type"] == "gap"
    assert items[0]["count"] == 30
    assert items[0]["from"] == 1 and items[0]["to"] == 30


def test_collapse_keeps_error_plus_context():
    # newest-first: 10 info, one err at index 10, 10 more info
    spec = [(20 - i, "info") for i in range(10)] + [(10, "err")] + [(9 - i, "info") for i in range(9)]
    items = logview.collapse(_rows(spec), ctx=5)
    kinds = [it["type"] for it in items]
    assert "gap" in kinds and any(it.get("lvl") == "err" for it in items if it["type"] == "line")
    # exactly 5 info kept on each side of the error are context-tagged
    ctx_lines = [it for it in items if it["type"] == "line" and it.get("ctx")]
    assert len(ctx_lines) == 10


def test_collapse_line_shape():
    items = logview.collapse(_rows([(5, "err")]))
    assert items[0]["type"] == "line"
    assert set(items[0]) >= {"id", "t", "lvl", "msg"}


def _add(session, cid, ts, lvl, msg="x"):
    row = LogLine(container_id=cid, source="mock", ts=ts, lvl=lvl, msg=msg)
    session.add(row); return row


def test_prune_keeps_errors_windows_info(session):
    now = 1_700_100_000.0
    cid = "ghstats-edge"
    for k in range(50):                          # 50 recent info
        _add(session, cid, now - k, "info")
    _add(session, cid, now - 5, "err")           # an error among them
    session.commit()
    deleted = logview.prune(session, cid, now, info_cap=10)
    rows = session.query(LogLine).filter_by(container_id=cid).all()
    assert any(r.lvl == "err" for r in rows)                      # error survives
    assert sum(1 for r in rows if r.lvl == "info") <= 10 + 11     # cap + ±5 context frozen
    assert deleted > 0


def test_prune_drops_beyond_7_days(session):
    now = 1_700_100_000.0
    cid = "ghstats-generator"
    session.query(LogLine).filter_by(container_id=cid).delete()  # clear seeded mock rows
    _add(session, cid, now - 8 * 86400, "err")   # 8d old error → gone by hard ceiling
    _add(session, cid, now - 60, "err")          # recent error → kept
    session.commit()
    logview.prune(session, cid, now)
    rows = session.query(LogLine).filter_by(container_id=cid).all()
    assert len(rows) == 1 and rows[0].ts == now - 60
