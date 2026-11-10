"""Product analytics for gh-stats and GPUFindr (the Analytics station).

Two sources feed tables that are never pruned, so history outlives gh-stats'
14-day event retention and Caddy's rolled logs:

* ``web_hits`` — browser requests to gh-stats.com / gpufindr.com, written by
  ``log_ingest`` from the Caddy access log (visits, time on site, searches).
* ``ghstats_*`` — gh-stats' own SQLite data (embed loads per user, OAuth),
  mirrored read-only by ``sync_ghstats``.

Every window is relative to the newest stored timestamp, never the wall clock,
so the seeded E2E data renders identically on every run.
"""
import glob
import gzip
import hashlib
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from sqlalchemy import func

from . import caddy_logs
from .models import GhstatsEvent, GhstatsUser, GhstatsUserDay, WebHit

SITES = {"ghstats": caddy_logs.GHSTATS_HOSTS, "gpufindr": caddy_logs.GPUFINDR_HOSTS}
EMBED_ENDPOINTS = ("/api/<u>", "/api/<u>/<widget>.svg", "/api/<widget>/<u>", "/api/top-langs")
LIVE_DAYS = 7
EMBED_MIN_DAYS = 2      # one-day users tried the editor; an embed loads on several days
TYPING_GAP = 10         # search-as-you-type: keep only the last query of a burst
SESSION_GAP = 1800
SEARCH_KEYS = ("name", "source", "location", "max_price", "min_flopsd")
SESSION_BUCKETS = [("<10s", 10), ("10s–1m", 60), ("1–3m", 180), ("3–10m", 600),
                   ("10–30m", 1800), ("30m+", None)]
LIFETIME_BUCKETS = [("<1 wk", 7), ("1–4 wk", 28), ("1–3 mo", 90), ("3–6 mo", 180), ("6 mo+", None)]
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_USER_PATH = re.compile(r"^/api/([A-Za-z0-9-]+)/(?:settings|me|data|generate|refresh)$")


def _tz():
    return ZoneInfo(os.environ.get("ANALYTICS_TZ", "America/New_York"))


# ---------------------------------------------------------------- ingest

def web_hit(line):
    """A Caddy JSON access line → an unsaved ``WebHit`` for a tracked site's
    browser traffic, or None (other hosts, crawlers, scripts, probes)."""
    try:
        rec = json.loads(line)
        req = rec["request"]
        host = req["host"].split(":", 1)[0]
        site = next((k for k, hosts in SITES.items() if host in hosts), None)
        if site is None:
            return None
        ua = (req.get("headers", {}).get("User-Agent") or [""])[0]
        if "Mozilla" not in ua or caddy_logs._BOT_UA.search(ua) or req["uri"].startswith(caddy_logs._PROBE_URIS):
            return None
        path, _, query = req["uri"].partition("?")
        ip = caddy_logs._client_ip(req)
        visitor = hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()[:12]
        return WebHit(site=site, ts=float(rec["ts"]), visitor=visitor, path=path[:300],
                      query=query[:1000], status=int(rec["status"]))
    except (ValueError, KeyError, TypeError):
        return None


def backfill_web(session, log_path):
    """One-time import of the rolled (gzipped) and live Caddy logs. Only hits
    older than what ``log_ingest`` already stored per site are added, so it is
    safe to re-run."""
    oldest = dict(session.query(WebHit.site, func.min(WebHit.ts)).group_by(WebHit.site).all())
    stem, ext = os.path.splitext(log_path)
    n = 0
    for path in sorted(glob.glob(f"{stem}-*{ext}.gz")) + [log_path]:
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                hit = web_hit(line)
                if hit and hit.ts < oldest.get(hit.site, float("inf")):
                    session.add(hit)
                    n += 1
    session.commit()
    return n


def _ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def sync_ghstats(session, data_dir):
    """Mirror gh-stats' users and new request events (read-only), and on the
    first run backfill per-user active days from its ``daily_stats`` rollup."""
    settings, events = os.path.join(data_dir, "settings.db"), os.path.join(data_dir, "analytics.db")
    if not (os.path.isfile(settings) and os.path.isfile(events)):
        return 0
    with _ro(settings) as s:
        users = s.execute("SELECT username, github_id IS NOT NULL, enrolled_at FROM users").fetchall()
    known = {u for u, _, _ in users}
    have = {u.username: u for u in session.query(GhstatsUser).all()}
    for name, oauth, enrolled in users:
        row = have.get(name)
        if row is None:
            session.add(GhstatsUser(username=name, oauth=bool(oauth), enrolled_at=enrolled))
        else:
            row.oauth = bool(oauth)
    last = session.query(func.max(GhstatsEvent.src_id)).scalar() or 0
    with _ro(events) as a:
        rows = a.execute(
            "SELECT id, ts, username, endpoint, widget FROM events WHERE id > ? AND kind = 'request' "
            "AND service = 'generator' AND username IS NOT NULL ORDER BY id", (last,)).fetchall()
        backfill = [] if session.query(GhstatsUserDay).first() else a.execute(
            "SELECT day, users_json FROM daily_stats").fetchall()
    n = 0
    for sid, ts, user, endpoint, widget in rows:
        if user in known:
            session.add(GhstatsEvent(src_id=sid, ts=float(ts), username=user,
                                     endpoint=endpoint or "", widget=widget))
            n += 1
    for day, users_json in backfill:
        for user in set(json.loads(users_json)) & known:
            session.add(GhstatsUserDay(username=user, day=day))
    session.commit()
    return n


# ---------------------------------------------------------------- helpers

def _day(ts, tz):
    return datetime.fromtimestamp(ts, tz).date()


def _days(start, end):
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _bucket(value, buckets):
    for label, hi in buckets:
        if hi is None or value < hi:
            return label


def _visits(sess):
    """Time-on-site histogram over engaged visits, plus the share that bounced
    (a single request, so no measurable duration)."""
    engaged = [s[2] for s in sess if s[3] > 1]
    return {"bounce": round(100 * (len(sess) - len(engaged)) / len(sess)) if sess else 0,
            "hist": _hist(engaged, SESSION_BUCKETS)}


def _hist(values, buckets):
    c = Counter(_bucket(v, buckets) for v in values)
    return [{"k": label, "v": c.get(label, 0)} for label, _ in buckets]


def _sessions(hits):
    """Per-visitor sessions as (visitor, start ts, duration s, hits)."""
    by = defaultdict(list)
    for h in hits:
        by[h.visitor].append(h.ts)
    out = []
    for v, ts in by.items():
        ts.sort()
        start = prev = ts[0]
        count = 1
        for t in ts[1:]:
            if t - prev > SESSION_GAP:
                out.append((v, start, prev - start, count))
                start, count = t, 0
            prev = t
            count += 1
        out.append((v, start, prev - start, count))
    return out


def _shape(stamps, now, start_day, tz):
    """Hourly: the 24 hours ending at ``now`` against the average day over the
    range. Weekly: the average count per weekday over the range."""
    now_dt = datetime.fromtimestamp(now, tz).replace(minute=0, second=0, microsecond=0)
    last = Counter()
    per_hour = Counter()
    per_day = Counter()
    for t in stamps:
        dt = datetime.fromtimestamp(t, tz)
        if dt.date() >= start_day:
            per_hour[dt.hour] += 1
            per_day[dt.date()] += 1
        back = int((now_dt - dt.replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600)
        if 0 <= back < 24:
            last[back] += 1
    first = min((datetime.fromtimestamp(t, tz).date() for t in stamps), default=start_day)
    days = _days(max(start_day, first), now_dt.date())
    hourly = []
    for back in range(23, -1, -1):
        h = (now_dt - timedelta(hours=back)).hour
        hourly.append({"h": f"{h:02d}:00", "last": last[back], "avg": round(per_hour[h] / len(days), 1)})
    weekly = []
    for wd, name in enumerate(WEEKDAYS):
        same = [d for d in days if d.weekday() == wd]
        weekly.append({"d": name, "v": round(sum(per_day[d] for d in same) / len(same), 1) if same else None})
    return hourly, weekly


def _start_day(now_day, range_days, earliest):
    if range_days:
        return now_day - timedelta(days=range_days - 1)
    return earliest or now_day


def _range_arg(raw):
    return {"7d": 7, "30d": 30, "90d": 90, "all": None}.get(raw, 30)


def _iso(d):
    return d.isoformat() if d else None


def _avg(xs):
    return round(sum(xs) / len(xs)) if xs else 0


# ---------------------------------------------------------------- gh-stats

def _ghstats_activity(session, tz):
    users = {u.username: u for u in session.query(GhstatsUser).all()}
    events = session.query(GhstatsEvent).filter(GhstatsEvent.endpoint.in_(EMBED_ENDPOINTS)).all()
    days = defaultdict(set)
    loads = defaultdict(Counter)                 # user -> day -> loads
    for e in events:
        d = _day(e.ts, tz)
        days[e.username].add(d)
        loads[e.username][d] += 1
    mirrored = min((_day(e.ts, tz) for e in events), default=None)
    for r in session.query(GhstatsUserDay).all():
        d = date.fromisoformat(r.day)
        if mirrored is None or d < mirrored:          # rollup also counts site visits; events are exact
            days[r.username].add(d)
    return users, events, days, loads


def _site_time_by_user(sessions_, hits):
    """Seconds on gh-stats.com per username, via visitors that touched a
    username-scoped page (``/api/<u>/settings`` and friends, ``/?username=``)."""
    owner = {}
    for h in hits:
        m = _USER_PATH.match(h.path)
        name = m.group(1) if m else (parse_qs(h.query).get("username") or [None])[0]
        if name:
            owner.setdefault(h.visitor, name)
    out = Counter()
    for v, _, dur, _ in sessions_:
        if v in owner:
            out[owner[v]] += dur
    return out


def ghstats_report(session, range_days):
    tz = _tz()
    users, events, days, loads = _ghstats_activity(session, tz)
    hits = session.query(WebHit).filter_by(site="ghstats").all()
    stamps = [e.ts for e in events]
    all_days = [d for ds in days.values() for d in ds]
    if not all_days:
        return {"empty": True}
    now = max(stamps + [h.ts for h in hits], default=None)
    now_day = max(all_days + ([_day(now, tz)] if now else []))
    if now is None:
        now = datetime.combine(now_day, datetime.max.time(), tz).timestamp()
    start = _start_day(now_day, range_days, min(all_days))
    span = _days(start, now_day)

    first = {u: min(ds) for u, ds in days.items()}
    lastd = {u: max(ds) for u, ds in days.items()}
    live_cut = now_day - timedelta(days=LIVE_DAYS - 1)
    embedders = {u for u, ds in days.items() if len(ds) >= EMBED_MIN_DAYS}

    active_by_day = Counter(d for ds in days.values() for d in ds)
    live_by_day = Counter()
    for u in embedders:
        ds = days[u]
        cover = set()
        for d in ds:
            cover.update(d + timedelta(days=i) for i in range(LIVE_DAYS))
        live_by_day.update(cover)
    oauth_by_day = Counter(d for u, ds in days.items() if users[u].oauth for d in ds)
    loads_by_day = Counter(_day(t, tz) for t in stamps)

    sess = [s for s in _sessions(hits) if _day(s[1], tz) >= start]
    sess_by_day = defaultdict(list)
    for s in sess:
        sess_by_day[_day(s[1], tz)].append(s[2])
    site_time = _site_time_by_user(_sessions(hits), hits)

    history = [{"d": _iso(d), "users": active_by_day[d], "live": live_by_day[d],
                "oauth": oauth_by_day[d], "loads": loads_by_day[d]} for d in span]
    in_range = {u for u, ds in days.items() if any(d >= start for d in ds)}
    event_days = [d for d in span if d >= min(loads_by_day, default=now_day)]

    weeks = defaultdict(lambda: {"started": 0, "stopped": 0})
    for u in embedders:
        if first[u] >= start:
            weeks[first[u] - timedelta(days=first[u].weekday())]["started"] += 1
        if lastd[u] < live_cut and lastd[u] >= start:
            weeks[lastd[u] - timedelta(days=lastd[u].weekday())]["stopped"] += 1
    week0 = start - timedelta(days=start.weekday())
    embeds = [{"w": _iso(w), **weeks[w]} for w in _days(week0, now_day)[::7]]

    hourly, weekly = _shape(stamps, now, start, tz)
    table = []
    for u in sorted(days, key=lambda u: (lastd[u], u), reverse=True):
        rng_loads = sum(c for d, c in loads[u].items() if d >= start)
        table.append({
            "id": u, "oauth": users[u].oauth,
            "status": ("tried" if u not in embedders
                       else "live" if lastd[u] >= live_cut else "stopped"),
            "first": _iso(first[u]), "last": _iso(lastd[u]),
            "embedded_days": (lastd[u] - first[u]).days + 1,
            "loads": rng_loads, "site_s": round(site_time.get(u, 0)),
        })
    return {
        "site": "ghstats", "now": _iso(now_day), "start": _iso(start),
        "tiles": [
            {"k": "active", "label": "Active users", "v": len(in_range),
             "spark": [h["users"] for h in history]},
            {"k": "live", "label": "Live embeds", "v": live_by_day[now_day],
             "spark": [h["live"] for h in history]},
            {"k": "time", "label": "Avg time on site", "v": _avg([s[2] for s in sess]), "unit": "s",
             "spark": [_avg(sess_by_day[d]) for d in span]},
            {"k": "loads", "label": "Embed loads / day",
             "v": _avg([loads_by_day[d] for d in event_days]),
             "spark": [loads_by_day[d] for d in span]},
        ],
        "history": history, "hourly": hourly, "weekly": weekly, "embeds": embeds,
        "lifetime": _hist([(lastd[u] - first[u]).days + 1 for u in embedders], LIFETIME_BUCKETS),
        "sessions": _visits(sess),
        "users": table,
    }


def ghstats_user(session, username):
    tz = _tz()
    users, events, days, loads = _ghstats_activity(session, tz)
    if username not in days:
        return None
    ds = sorted(days[username])
    widgets = Counter(e.widget or e.endpoint for e in events if e.username == username)
    return {
        "id": username, "oauth": users[username].oauth, "enrolled": users[username].enrolled_at[:10],
        "timeline": [{"d": _iso(d), "v": loads[username][d], "on": d in days[username]}
                     for d in _days(ds[0], ds[-1])],
        "top": [{"k": k, "v": v} for k, v in widgets.most_common(6)],
    }


# ---------------------------------------------------------------- GPUFindr

def _search(hit):
    if hit.path != "/gpus":
        return None
    q = parse_qs(hit.query)
    s = {k: q[k][0].strip().lower() for k in SEARCH_KEYS if q.get(k) and q[k][0].strip()}
    return s or None


def _searches(hits):
    """(hit, search) pairs, keeping only the last query of each typing burst."""
    found = [(h, s) for h in hits if (s := _search(h))]
    last = {}
    for i, (h, _) in enumerate(found):
        prev = last.get(h.visitor)
        if prev is not None and h.ts - found[prev][0].ts <= TYPING_GAP:
            found[prev] = None
        last[h.visitor] = i
    return [f for f in found if f]


def gpufindr_report(session, range_days):
    tz = _tz()
    hits = session.query(WebHit).filter_by(site="gpufindr").order_by(WebHit.ts).all()
    if not hits:
        return {"empty": True}
    now = hits[-1].ts
    now_day = _day(now, tz)
    start = max(_start_day(now_day, range_days, _day(hits[0].ts, tz)), _day(hits[0].ts, tz))
    span = _days(start, now_day)
    rng = [h for h in hits if _day(h.ts, tz) >= start]
    live_cut = now_day - timedelta(days=LIVE_DAYS - 1)

    sess_all = _sessions(hits)
    sess = [s for s in sess_all if _day(s[1], tz) >= start]
    visitors_by_day = defaultdict(set)
    for h in rng:
        visitors_by_day[_day(h.ts, tz)].add(h.visitor)
    searches = _searches(rng)
    search_by_day = Counter(_day(h.ts, tz) for h, _ in searches)
    sess_by_day = defaultdict(list)
    for s in sess:
        sess_by_day[_day(s[1], tz)].append(s[2])

    per = defaultdict(lambda: {"visits": 0, "time": 0.0, "first": None, "last": None,
                               "searches": 0, "gpus": Counter(), "providers": Counter()})
    for v, st, dur, _ in sess_all:
        p = per[v]
        d = _day(st, tz)
        p["first"] = min(p["first"] or d, d)
        p["last"] = max(p["last"] or d, d)
        if d >= start:
            p["visits"] += 1
            p["time"] += dur
    for h, s in searches:
        p = per[h.visitor]
        p["searches"] += 1
        if "name" in s:
            p["gpus"][s["name"]] += 1
        if "source" in s:
            p["providers"][s["source"]] += 1
    gpus = Counter(s["name"] for _, s in searches if "name" in s)
    providers = Counter(s["source"] for _, s in searches if "source" in s)

    table = []
    for v, p in sorted(per.items(), key=lambda kv: (kv[1]["last"], kv[1]["visits"], kv[0]), reverse=True):
        if p["last"] < start:
            continue
        table.append({
            "id": v, "status": "live" if p["last"] >= live_cut else "stopped",
            "first": _iso(p["first"]), "last": _iso(p["last"]), "visits": p["visits"],
            "searches": p["searches"], "site_s": round(p["time"]),
            "gpu": (p["gpus"].most_common(1) or [[None]])[0][0],
            "provider": (p["providers"].most_common(1) or [[None]])[0][0],
        })
    hourly, weekly = _shape([h.ts for h in hits], now, start, tz)
    return {
        "site": "gpufindr", "now": _iso(now_day), "start": _iso(start),
        "tiles": [
            {"k": "visitors", "label": "Visitors", "v": len({h.visitor for h in rng}),
             "spark": [len(visitors_by_day[d]) for d in span]},
            {"k": "visits", "label": "Visits / day", "v": _avg([len(sess_by_day[d]) for d in span]),
             "spark": [len(sess_by_day[d]) for d in span]},
            {"k": "time", "label": "Avg time on site", "v": _avg([s[2] for s in sess]), "unit": "s",
             "spark": [_avg(sess_by_day[d]) for d in span]},
            {"k": "searches", "label": "Searches / day", "v": _avg([search_by_day[d] for d in span]),
             "spark": [search_by_day[d] for d in span]},
        ],
        "history": [{"d": _iso(d), "visitors": len(visitors_by_day[d]), "searches": search_by_day[d]}
                    for d in span],
        "hourly": hourly, "weekly": weekly,
        "gpus": [{"k": k, "v": v} for k, v in gpus.most_common(8)],
        "providers": [{"k": k, "v": v} for k, v in providers.most_common(8)],
        "sessions": _visits(sess),
        "users": table,
    }


def gpufindr_user(session, visitor):
    tz = _tz()
    hits = session.query(WebHit).filter_by(site="gpufindr", visitor=visitor).order_by(WebHit.ts).all()
    if not hits:
        return None
    per_day = Counter(_day(h.ts, tz) for h in hits)
    days = sorted(per_day)
    combos = Counter(" · ".join(f"{k}={v}" for k, v in s.items()) for _, s in _searches(hits))
    return {
        "id": visitor,
        "timeline": [{"d": _iso(d), "v": per_day[d], "on": d in per_day} for d in _days(days[0], days[-1])],
        "top": [{"k": k, "v": v} for k, v in combos.most_common(8)],
    }


REPORTS = {"ghstats": ghstats_report, "gpufindr": gpufindr_report}
USERS = {"ghstats": ghstats_user, "gpufindr": gpufindr_user}


def main(argv):  # pragma: no cover - operator CLI
    """``python -m app.analytics backfill`` | ``sync`` — one-shot imports."""
    from . import create_app
    app = create_app()
    if argv[:1] == ["backfill"]:
        print("web hits:", backfill_web(app.db_session, os.environ["CADDY_ACCESS_LOG"]))
    print("ghstats events:", sync_ghstats(app.db_session, os.environ["GHSTATS_DATA_DIR"]))


if __name__ == "__main__":  # pragma: no cover
    import sys
    main(sys.argv[1:])
