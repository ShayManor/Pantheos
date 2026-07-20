"""Standalone tail→DB ingest of each container's stdout/stderr (prod only).

Sibling of ``log_ingest`` (which tails the Caddy *access* log): this reads the
containers' own stdout/stderr from Docker's ``json-file`` driver — the files under
``/var/lib/docker/containers/<hash>/<hash>-json.log`` — so every container in the
monitoring ``INVENTORY`` gets real log lines, not just the vhost-fronted ones.
Runs as ``python -m app.docker_log_ingest`` with ``/var/lib/docker`` mounted
read-only (same mount cAdvisor uses). Each file keeps a per-path (inode, offset)
cursor in ``IngestState`` so restarts resume without dupes and rotation restarts
from 0. Never runs in dev/CI/E2E — those read seeded ``mock`` rows — so the
deterministic test gate is unaffected. Only the serve loop is uncovered.
"""
import os
import time

from . import docker_logs, logview
from .models import IngestState, LogLine
from .monitor_inventory import INVENTORY


def container_targets(root):
    """(container_id, json_log_path) for each INVENTORY container with a log file."""
    cdir = os.path.join(root, "containers")
    try:
        hashes = os.listdir(cdir)
    except OSError:
        return []
    targets = []
    for chash in sorted(hashes):
        try:
            with open(os.path.join(cdir, chash, "config.v2.json")) as f:
                name = docker_logs.name_from_config(f.read())
        except OSError:
            continue
        if name not in INVENTORY:
            continue
        log_path = os.path.join(cdir, chash, f"{chash}-json.log")
        if os.path.isfile(log_path):
            targets.append((name, log_path))
    return targets


def ingest_once(session, path, container_id):
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
    count = 0
    for line in consumed.decode("utf-8", "replace").splitlines():
        rec = docker_logs.parse_line(line)
        if not rec:
            continue
        session.add(LogLine(
            container_id=container_id, source="docker", ts=rec["ts"],
            lvl=docker_logs.level(rec["msg"]), msg=rec["msg"]))
        count += 1
    if st is None:
        session.add(IngestState(path=path, inode=inode, offset=new_offset))
    else:
        st.inode, st.offset = inode, new_offset
    session.commit()
    return count


def run_once(session, root, now):
    total = 0
    for cid, path in container_targets(root):
        total += ingest_once(session, path, cid)
        logview.prune(session, cid, now)
    return total


def serve():  # pragma: no cover - process loop
    from . import create_app
    app = create_app()
    root = os.environ.get("DOCKER_ROOT", "/var/lib/docker")
    interval = int(os.environ.get("LOG_INGEST_INTERVAL", "5"))
    while True:
        run_once(app.db_session, root, time.time())
        app.db_session.remove()
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover
    serve()
