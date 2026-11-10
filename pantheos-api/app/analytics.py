"""Product analytics for gh-stats and GPUFindr (the Analytics station).

Two sources feed tables that are never pruned, so history outlives gh-stats'
14-day event retention and Caddy's rolled logs:

* ``web_hits`` — browser requests to gh-stats.com / gpufindr.com, written by
  ``log_ingest`` from the Caddy access log (visits, time on site, searches).
* ``ghstats_loads`` — widget fetches by GitHub's image proxy (github-camo),
  also from the Caddy log. Only a widget in a real README gets fetched by
  camo, so these alone decide who embeds; scanner-made "users" (``/api/env``)
  and editor previews never count.
* ``ghstats_users`` — gh-stats' enrolled users (OAuth, enrolment date),
  mirrored read-only by ``sync_ghstats``.

Embed history starts at the first stored proxy fetch (``tracked_from``); the
report never guesses about the time before it.

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
from contextlib import closing
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from sqlalchemy import func

from . import caddy_logs
from .models import GhstatsLoad, GhstatsUser, WebHit

SITES = {"ghstats": caddy_logs.GHSTATS_HOSTS, "gpufindr": caddy_logs.GPUFINDR_HOSTS}
LIVE_DAYS = 7
TYPING_GAP = 10         # search-as-you-type: keep only the last query of a burst
SESSION_GAP = 1800
SEARCH_KEYS = ("name", "source", "location", "max_price", "min_flopsd")
SESSION_BUCKETS = [("<10s", 10), ("10s–1m", 60), ("1–3m", 180), ("3–10m", 600),
                   ("10–30m", 1800), ("30m+", None)]
LIFETIME_BUCKETS = [("<1 wk", 7), ("1–4 wk", 28), ("1–3 mo", 90), ("3–6 mo", 180), ("6 mo+", None)]
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_USER_PATH = re.compile(r"^/api/([A-Za-z0-9-]+)/(?:settings|me|data|generate|refresh)$")
_GH_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38})$")


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


def embed_load(line):
    """A Caddy JSON access line → an unsaved ``GhstatsLoad`` when GitHub's image
    proxy fetched a gh-stats widget, else None. The username comes from
    ``?username=`` (``/api``, ``/api/top-langs``, ``/``) or the path
    (``/api/<u>``, ``/api/<u>/<widget>.svg``, ``/api/<widget>/<u>``)."""
    try:
        rec = json.loads(line)
        req = rec["request"]
        ua = (req.get("headers", {}).get("User-Agent") or [""])[0]
        if (req["host"].split(":", 1)[0] not in caddy_logs.GHSTATS_HOSTS or not ua.startswith("github-camo")
                or int(rec["status"]) >= 400):
            return None
        path, _, query = req["uri"].partition("?")
        segs = [p for p in path.split("/") if p][1:] if path.startswith("/api") else []
        named = (parse_qs(query).get("username") or [None])[0]
        if named:
            user, widget = named, segs[0] if segs else "stats"
        elif len(segs) == 1:
            user, widget = segs[0], "composite"
        elif len(segs) == 2 and segs[1].endswith(".svg"):
            user, widget = segs[0], segs[1][:-4]
        elif len(segs) == 2:
            user, widget = segs[1], segs[0]
        else:
            return None
        user = user.strip().lower()
        if not _GH_NAME.match(user):
            return None
        return GhstatsLoad(ts=float(rec["ts"]), username=user, widget=widget[:40])
    except (ValueError, KeyError, TypeError):
        return None


def records(line):
    """Every analytics row one access line produces (for ``log_ingest``)."""
    return [r for r in (web_hit(line), embed_load(line)) if r is not None]


def _key(row):
    return row.site if isinstance(row, WebHit) else "embed"


def backfill_web(session, log_path):
    """One-time import of the rolled (gzipped) and live Caddy logs. Only rows
    older than what ``log_ingest`` already stored are added, so it is safe to
    re-run."""
    oldest = dict(session.query(WebHit.site, func.min(WebHit.ts)).group_by(WebHit.site).all())
    oldest["embed"] = session.query(func.min(GhstatsLoad.ts)).scalar() or float("inf")
    stem, ext = os.path.splitext(log_path)
    n = 0
    for path in sorted(glob.glob(f"{stem}-*{ext}.gz")) + [log_path]:
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                for row in records(line):
                    if row.ts < oldest.get(_key(row), float("inf")):
                        session.add(row)
                        n += 1
    session.commit()
    return n


def _ro(path):
    """Read-only connection that closes on exit (sqlite3's own context manager only commits)."""
    return closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True))


def sync_ghstats(session, data_dir):
    """Mirror gh-stats' enrolled users (read-only). Returns the rows added."""
    settings = os.path.join(data_dir, "settings.db")
    if not os.path.isfile(settings):
        return 0
    with _ro(settings) as s:
        users = s.execute("SELECT username, github_id IS NOT NULL, enrolled_at FROM users").fetchall()
    have = {u.username: u for u in session.query(GhstatsUser).all()}
    n = 0
    for name, oauth, enrolled in users:
        row = have.get(name)
        if row is None:
            session.add(GhstatsUser(username=name, oauth=bool(oauth), enrolled_at=enrolled))
            n += 1
        else:
            row.oauth = bool(oauth)
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
    """Embedders are the usernames GitHub's image proxy fetched at least once;
    their days are the days it fetched them."""
    users = {u.username.lower(): u for u in session.query(GhstatsUser).all()}
    loads = session.query(GhstatsLoad).all()
    counts = defaultdict(Counter)                # user -> day -> proxy fetches
    for ld in loads:
        counts[ld.username][_day(ld.ts, tz)] += 1
    return users, loads, counts


def _site_time_by_user(sessions_, hits):
    """Seconds on gh-stats.com per username, via visitors that touched a
    username-scoped page (``/api/<u>/settings`` and friends, ``/?username=``)."""
    owner = {}
    for h in hits:
        m = _USER_PATH.match(h.path)
        name = m.group(1) if m else (parse_qs(h.query).get("username") or [None])[0]
        if name:
            owner.setdefault(h.visitor, name.lower())
    out = Counter()
    for v, _, dur, _ in sessions_:
        if v in owner:
            out[owner[v]] += dur
    return out


def ghstats_report(session, range_days):
    tz = _tz()
    users, loads, counts = _ghstats_activity(session, tz)
    days = {u: set(c) for u, c in counts.items()}
    if not loads:
        return {"empty": True}
    hits = session.query(WebHit).filter_by(site="ghstats").all()
    stamps = [ld.ts for ld in loads]
    now = max(stamps + [h.ts for h in hits])
    now_day = _day(now, tz)
    tracked = _day(min(stamps), tz)
    # A live README gets fetched within a week, so anyone first seen in the
    # first week of tracking was most likely already embedding.
    warm = tracked + timedelta(days=LIVE_DAYS - 1)
    start = _start_day(now_day, range_days, tracked)
    span = _days(start, now_day)
    first = {u: min(ds) for u, ds in days.items()}
    lastd = {u: max(c) for u, c in counts.items()}           # last proxy fetch decides live/stopped
    live_cut = now_day - timedelta(days=LIVE_DAYS - 1)

    active_by_day = Counter(d for ds in days.values() for d in ds)
    live_by_day = Counter()
    for ds in days.values():
        cover = set()
        for d in ds:
            cover.update(d + timedelta(days=i) for i in range(LIVE_DAYS))
        live_by_day.update(cover)
    loads_by_day = Counter(_day(t, tz) for t in stamps)
    logged = [d for d in span if d >= tracked]

    sess = [s for s in _sessions(hits) if _day(s[1], tz) >= start]
    sess_by_day = defaultdict(list)
    for s in sess:
        sess_by_day[_day(s[1], tz)].append(s[2])
    site_time = _site_time_by_user(_sessions(hits), hits)

    weeks = defaultdict(lambda: {"started": 0, "stopped": 0})
    for u in days:
        if first[u] >= start and first[u] > warm:
            weeks[first[u] - timedelta(days=first[u].weekday())]["started"] += 1
        if start <= lastd[u] < live_cut:
            weeks[lastd[u] - timedelta(days=lastd[u].weekday())]["stopped"] += 1
    week0 = start - timedelta(days=start.weekday())
    hourly, weekly = _shape(stamps, now, start, tz)

    def name(u):
        return users[u].username if u in users else u

    table = [{
        "id": name(u), "oauth": bool(u in users and users[u].oauth),
        "status": "live" if lastd[u] >= live_cut else "stopped",
        "first": _iso(first[u]), "last": _iso(lastd[u]),
        "embedded_days": (lastd[u] - first[u]).days + 1, "since_tracking": first[u] <= warm,
        "loads": sum(c for d, c in counts[u].items() if d >= start), "site_s": round(site_time.get(u, 0)),
    } for u in sorted(days, key=lambda u: (lastd[u], u), reverse=True)]
    table += [{
        "id": users[u].username, "oauth": users[u].oauth, "status": "none",
        "first": users[u].enrolled_at[:10], "last": None, "embedded_days": 0, "since_tracking": False, "loads": 0,
        "site_s": round(site_time.get(u, 0)),
    } for u in sorted(set(users) - set(days), key=lambda u: (users[u].enrolled_at, u), reverse=True)]

    return {
        "site": "ghstats", "now": _iso(now_day), "start": _iso(start), "tracked_from": _iso(tracked),
        "tiles": [
            {"k": "embedders", "label": "Embedding users",
             "v": sum(1 for ds in days.values() if max(ds) >= start),
             "spark": [active_by_day[d] if d >= tracked else None for d in span]},
            {"k": "live", "label": "Live embeds", "v": live_by_day[now_day],
             "spark": [live_by_day[d] if d >= warm else None for d in span]},
            {"k": "time", "label": "Avg time on site", "v": _avg([s[2] for s in sess]), "unit": "s",
             "spark": [_avg(sess_by_day[d]) for d in span]},
            {"k": "loads", "label": "Embed loads / day", "v": _avg([loads_by_day[d] for d in logged]),
             "spark": [loads_by_day[d] if d >= tracked else None for d in span]},
        ],
        # Untracked days are null, not zero. "live" needs a full window of tracking.
        "history": [{"d": _iso(d), "users": active_by_day[d] if d >= tracked else None,
                     "live": live_by_day[d] if d >= warm else None,
                     "loads": loads_by_day[d] if d >= tracked else None} for d in span],
        "hourly": hourly, "weekly": weekly,
        "embeds": [{"w": _iso(w), **weeks[w]} for w in _days(week0, now_day)[::7]
                   if w + timedelta(days=6) >= tracked],
        "lifetime": _hist([(lastd[u] - first[u]).days + 1 for u in days], LIFETIME_BUCKETS),
        "sessions": _visits(sess),
        "users": table,
    }


def ghstats_user(session, username):
    tz = _tz()
    users, loads, counts = _ghstats_activity(session, tz)
    u = username.lower()
    if u not in counts and u not in users:
        return None
    ds = sorted(counts.get(u, ()))
    out = {"id": username, "oauth": bool(u in users and users[u].oauth),
           "enrolled": users[u].enrolled_at[:10] if u in users else None, "timeline": [], "top": []}
    if ds:
        out["timeline"] = [{"d": _iso(d), "v": counts[u][d]} for d in _days(ds[0], ds[-1])]
        out["top"] = [{"k": k, "v": v} for k, v in Counter(ld.widget for ld in loads if ld.username == u).most_common(6)]
    return out


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
    print("ghstats rows:", sync_ghstats(app.db_session, os.environ["GHSTATS_DATA_DIR"]))


if __name__ == "__main__":  # pragma: no cover
    import sys
    main(sys.argv[1:])
