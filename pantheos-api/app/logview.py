"""Pure log-view transforms: raw-line shaping, smart collapse, and retention.

``collapse`` turns an ordered (newest-first) run of stored log rows into display
*items* — every err/warn plus ±``ctx`` info lines of context, with the remaining
info runs folded into expandable ``gap`` markers. ``prune`` is the storage-side
counterpart (errors kept, info windowed). No randomness or wall-clock here.
"""
from . import caddy_logs
from .models import LogLine


def line(row):
    return {"id": row.id, "t": caddy_logs._hhmmss(row.ts), "lvl": row.lvl, "msg": row.msg}


def collapse(rows, ctx=5):
    n = len(rows)
    keep = [i for i in range(n) if rows[i].lvl in ("err", "warn")]
    ctxset = set()
    for i in keep:
        for j in range(max(0, i - ctx), min(n, i + ctx + 1)):
            if rows[j].lvl == "info":
                ctxset.add(j)
    visible = set(keep) | ctxset
    items, run = [], []

    def flush():
        if run:
            ids = [rows[k].id for k in run]
            items.append({"type": "gap", "count": len(run), "from": min(ids), "to": max(ids)})
            run.clear()

    for i in range(n):
        if i in visible:
            flush()
            item = {"type": "line", **line(rows[i])}
            if i in ctxset and rows[i].lvl == "info":
                item["ctx"] = True
            items.append(item)
        else:
            run.append(i)
    flush()
    return items


def prune(session, container_id, now, info_cap=2000, ctx=5, ttl_days=7):
    cutoff = now - ttl_days * 86400
    q = session.query(LogLine).filter(LogLine.container_id == container_id)
    deleted = 0
    for r in q.filter(LogLine.ts < cutoff).all():   # 1. hard 7d ceiling, all levels
        session.delete(r); deleted += 1
    rows = q.filter(LogLine.ts >= cutoff).order_by(LogLine.id).all()
    n = len(rows)
    keep_info = set()
    for i in range(n):                              # 2. info within ±ctx of an err/warn
        if rows[i].lvl in ("err", "warn"):
            for j in range(max(0, i - ctx), min(n, i + ctx + 1)):
                if rows[j].lvl == "info":
                    keep_info.add(rows[j].id)
    info_ids = [r.id for r in rows if r.lvl == "info"]
    keep_info |= set(info_ids[-info_cap:])          # 3. most-recent info_cap info
    for r in rows:                                  # err/warn never pruned within 7d
        if r.lvl == "info" and r.id not in keep_info:
            session.delete(r); deleted += 1
    session.commit()
    return deleted
