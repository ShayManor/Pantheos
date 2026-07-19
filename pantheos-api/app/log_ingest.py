"""Standalone tail→DB ingest of the real Caddy access log (prod only).

Sibling to ``caddy_exporter``: runs as ``python -m app.log_ingest`` with the access
log mounted read-only. It appends parsed request lines as ``source="caddy"`` rows,
tracking a per-path (inode, byte-offset) cursor so restarts resume without dupes and
log rotation (inode change) restarts from 0. Each cycle also prunes (retention). This
process never runs in dev/CI/E2E — those read seeded ``mock`` rows — so the
deterministic test gate is unaffected. Only the serve loop is uncovered.
"""
import os
import time

from . import caddy_logs, logview
from .models import IngestState, LogLine
from .monitor_inventory import INVENTORY


def _host_container_map():
    return [(cid, set(e["hosts"])) for cid, e in INVENTORY.items() if e.get("hosts")]


def _route(host, mapping):
    for cid, hosts in mapping:
        if host in hosts:
            return cid
    return None


def ingest_once(session, path):
    try:
        inode = os.stat(path).st_ino
    except OSError:
        return 0
    st = session.get(IngestState, path)
    offset = st.offset if st and st.inode == inode else 0
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        if offset > f.tell():          # truncated in place
            offset = 0
        f.seek(offset)
        data = f.read()
    nl = data.rfind(b"\n")
    consumed = data[:nl + 1] if nl != -1 else b""
    new_offset = offset + (nl + 1 if nl != -1 else 0)
    mapping = _host_container_map()
    count = 0
    for line in consumed.decode("utf-8", "replace").splitlines():
        rec = caddy_logs.parse_record(line)
        if not rec:
            continue
        cid = _route(rec["host"], mapping)
        if not cid:
            continue
        session.add(LogLine(
            container_id=cid, source="caddy", ts=rec["ts"],
            lvl=caddy_logs._level(rec["status"]),
            msg=f'{rec["method"]} {rec["uri"]} {rec["status"]} {round(rec["dur"] * 1000)}ms'))
        count += 1
    if st is None:
        session.add(IngestState(path=path, inode=inode, offset=new_offset))
    else:
        st.inode, st.offset = inode, new_offset
    session.commit()
    return count


def prune_all(session, now):
    cids = [c for (c,) in session.query(LogLine.container_id)
            .filter_by(source="caddy").distinct()]
    for cid in cids:
        logview.prune(session, cid, now)


def run_once(session, path, now):
    n = ingest_once(session, path)
    prune_all(session, now)
    return n


def serve():  # pragma: no cover - process loop
    from . import create_app
    app = create_app()
    path = os.environ.get("CADDY_ACCESS_LOG")
    interval = int(os.environ.get("LOG_INGEST_INTERVAL", "5"))
    while True:
        run_once(app.db_session, path, time.time())
        app.db_session.remove()
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover
    serve()
