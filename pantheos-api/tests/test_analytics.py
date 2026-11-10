import gzip
import json
import sqlite3

from app import analytics, log_ingest
from app.models import GhstatsEvent, GhstatsUser, GhstatsUserDay, WebHit
from app.sample_data import ANALYTICS_NOW

UA = "Mozilla/5.0 (Macintosh) Safari"


def _line(host, uri, ts=1e9, ua=UA, ip="1.2.3.4"):
    return json.dumps({"ts": ts, "duration": 0.01, "status": 200, "request": {
        "method": "GET", "host": host, "uri": uri, "client_ip": ip,
        "headers": {"User-Agent": [ua]}}})


# ---------------------------------------------------------------- ingest

def test_web_hit_keeps_browser_traffic_on_tracked_sites():
    h = analytics.web_hit(_line("gpufindr.com", "/gpus?name=h100"))
    assert (h.site, h.path, h.query, len(h.visitor)) == ("gpufindr", "/gpus", "name=h100", 12)
    assert analytics.web_hit(_line("www.gh-stats.com:443", "/")).site == "ghstats"


def test_web_hit_drops_other_hosts_bots_probes_and_junk():
    assert analytics.web_hit(_line("pantheos.app", "/")) is None
    assert analytics.web_hit(_line("gpufindr.com", "/", ua="Googlebot Mozilla")) is None
    assert analytics.web_hit(_line("gpufindr.com", "/", ua="curl/8")) is None
    assert analytics.web_hit(_line("gpufindr.com", "/.env")) is None
    assert analytics.web_hit("not json") is None


def test_visitor_hash_separates_ip_and_ua():
    a = analytics.web_hit(_line("gpufindr.com", "/", ip="1.1.1.1")).visitor
    b = analytics.web_hit(_line("gpufindr.com", "/", ip="2.2.2.2")).visitor
    assert a != b and "1.1.1.1" not in a


def test_log_ingest_also_stores_web_hits(session, tmp_path):
    p = tmp_path / "access.log"
    p.write_text(_line("gpufindr.com", "/", ts=5e9) + "\n")
    log_ingest.ingest_once(session, str(p))
    assert session.query(WebHit).filter_by(ts=5e9).count() == 1


def test_backfill_web_reads_rolled_logs_once(session, tmp_path):
    live = tmp_path / "access.log"
    live.write_text(_line("gpufindr.com", "/", ts=10.0) + "\n")
    with gzip.open(tmp_path / "access-2026-01-01.log.gz", "wt") as f:
        f.write(_line("gpufindr.com", "/", ts=5.0) + "\n" + _line("pantheos.app", "/", ts=6.0) + "\n")
    assert analytics.backfill_web(session, str(live)) == 2
    assert analytics.backfill_web(session, str(live)) == 0      # older than what's stored → skipped


def _ghstats_dir(tmp_path):
    s = sqlite3.connect(tmp_path / "settings.db")
    s.execute("CREATE TABLE users (username TEXT, github_id INTEGER, enrolled_at TEXT)")
    s.executemany("INSERT INTO users VALUES (?,?,?)",
                  [("newbie", 7, "2026-01-01T00:00:00Z"), ("octocat", None, "2026-01-01T00:00:00Z")])
    s.commit(); s.close()
    a = sqlite3.connect(tmp_path / "analytics.db")
    a.execute("CREATE TABLE events (id INTEGER, ts INTEGER, service TEXT, kind TEXT, username TEXT,"
              " endpoint TEXT, widget TEXT)")
    a.executemany("INSERT INTO events VALUES (?,?,?,?,?,?,?)", [
        (1, 100, "generator", "request", "newbie", "/api/<u>", None),
        (2, 101, "generator", "request", ".env", "/api/<u>", None),          # junk username
        (3, 102, "fetcher", "fetch", "newbie", "github", None),
        (4, 103, "generator", "request", "newbie", None, None)])
    a.execute("CREATE TABLE daily_stats (day TEXT, users_json TEXT)")
    a.execute("INSERT INTO daily_stats VALUES ('2026-01-02', ?)", (json.dumps(["newbie", "junk"]),))
    a.commit(); a.close()
    return str(tmp_path)


def test_sync_ghstats_mirrors_users_events_and_backfill(session, tmp_path):
    session.query(GhstatsEvent).delete()                                    # a fresh mirror
    session.query(GhstatsUserDay).delete()
    session.commit()
    d = _ghstats_dir(tmp_path)
    assert analytics.sync_ghstats(session, d) == 2
    assert session.get(GhstatsUser, "newbie").oauth is True
    assert session.get(GhstatsUser, "octocat").oauth is False                # existing row updated
    assert session.query(GhstatsEvent).count() == 2
    assert session.get(GhstatsUserDay, ("newbie", "2026-01-02")) is not None
    assert analytics.sync_ghstats(session, d) == 0                          # incremental
    assert analytics.sync_ghstats(session, str(tmp_path / "missing")) == 0


# ---------------------------------------------------------------- reports

def test_ghstats_report_shape(client):
    r = client.get("/api/analytics/ghstats?range=30d").get_json()
    assert r["now"] == "2026-11-10"
    labels = [t["label"] for t in r["tiles"]]
    assert labels == ["Active users", "Live embeds", "Avg time on site", "Embed loads / day"]
    assert len(r["history"]) == 30 and len(r["hourly"]) == 24 and len(r["weekly"]) == 7
    assert 0 <= r["sessions"]["bounce"] <= 100 and len(r["sessions"]["hist"]) == 6
    assert r["hourly"][-1]["h"] == "15:00"
    statuses = {u["status"] for u in r["users"]}
    assert statuses == {"live", "stopped", "tried"}
    live = sum(u["status"] == "live" for u in r["users"])
    assert r["tiles"][1]["v"] == live
    assert any(u["site_s"] > 0 for u in r["users"])                         # visitor → username link
    assert sum(b["v"] for b in r["lifetime"]) == sum(u["status"] != "tried" for u in r["users"])


def test_ghstats_report_ranges(client):
    all_ = client.get("/api/analytics/ghstats?range=all").get_json()
    week = client.get("/api/analytics/ghstats?range=7d").get_json()
    assert len(all_["history"]) > len(week["history"]) == 7
    assert all_["tiles"][0]["v"] >= week["tiles"][0]["v"]


def test_ghstats_report_backfill_only(session):
    session.query(GhstatsEvent).delete()
    session.query(WebHit).delete()
    session.commit()
    r = analytics.ghstats_report(session, 7)
    assert r["tiles"][3]["v"] == 0 and r["hourly"][0]["last"] == 0


def test_reports_empty(session):
    for m in (GhstatsEvent, GhstatsUserDay, WebHit):
        session.query(m).delete()
    session.commit()
    assert analytics.ghstats_report(session, 30) == {"empty": True}
    assert analytics.gpufindr_report(session, 30) == {"empty": True}


def test_gpufindr_report_shape(client):
    r = client.get("/api/analytics/gpufindr").get_json()
    assert [t["label"] for t in r["tiles"]] == ["Visitors", "Visits / day", "Avg time on site", "Searches / day"]
    assert r["gpus"][0]["v"] >= r["gpus"][-1]["v"] and r["providers"]
    assert {u["status"] for u in r["users"]} <= {"live", "stopped"}
    assert any(u["gpu"] for u in r["users"])


def test_gpufindr_collapses_typing_and_hides_old_visitors(session):
    v = "typist"
    for ts, q in ((ANALYTICS_NOW, "name=r"), (ANALYTICS_NOW + 2, "name=rt"),
                  (ANALYTICS_NOW + 4, "name=RTX%205090"), (ANALYTICS_NOW + 4000, "location=us"),
                  (ANALYTICS_NOW + 4100, "limit=10")):
        session.add(WebHit(site="gpufindr", ts=ts, visitor=v, path="/gpus", query=q, status=200))
    session.add(WebHit(site="gpufindr", ts=ANALYTICS_NOW - 40 * 86400, visitor="ancient", path="/",
                       query="", status=200))
    session.commit()
    u = analytics.gpufindr_user(session, v)
    assert u["top"] == [{"k": "name=rtx 5090", "v": 1}, {"k": "location=us", "v": 1}]
    ids = [x["id"] for x in analytics.gpufindr_report(session, 7)["users"]]
    assert v in ids and "ancient" not in ids


def test_user_detail_endpoints(client):
    g = client.get("/api/analytics/ghstats/users/octocat").get_json()
    assert g["id"] == "octocat" and g["timeline"] and g["top"]
    v = client.get("/api/analytics/gpufindr").get_json()["users"][0]["id"]
    assert client.get(f"/api/analytics/gpufindr/users/{v}").get_json()["timeline"]
    assert client.get("/api/analytics/ghstats/users/nobody").status_code == 404
    assert client.get("/api/analytics/gpufindr/users/nobody").status_code == 404
    assert client.get("/api/analytics/nope/users/x").status_code == 404
    assert client.get("/api/analytics/nope").status_code == 404


def test_shape_leaves_weekdays_without_data_empty():
    tz = analytics._tz()
    today = analytics._day(ANALYTICS_NOW, tz)
    _, weekly = analytics._shape([ANALYTICS_NOW], ANALYTICS_NOW, today, tz)
    assert sum(w["v"] is None for w in weekly) == 6


def test_backfill_days_after_mirroring_are_ignored(session):
    session.add(GhstatsUserDay(username="tj", day="2026-11-09"))           # inside the events window
    session.commit()
    u = analytics.ghstats_user(session, "tj")
    assert "2026-11-09" not in [d["d"] for d in u["timeline"] if d["on"] and not d["v"]]
