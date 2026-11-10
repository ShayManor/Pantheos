import gzip
import json
import sqlite3

from app import analytics, log_ingest
from app.models import GhstatsLoad, GhstatsUser, WebHit
from app.sample_data import ANALYTICS_NOW

UA = "Mozilla/5.0 (Macintosh) Safari"
CAMO = "github-camo (ea45cab4)"


def _line(host, uri, ts=1e9, ua=UA, ip="1.2.3.4", status=200):
    return json.dumps({"ts": ts, "duration": 0.01, "status": status, "request": {
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


def _load(uri, **kw):
    ld = analytics.embed_load(_line("gh-stats.com", uri, ua=CAMO, **kw))
    return ld and (ld.username, ld.widget)


def test_embed_load_reads_the_username_from_every_widget_url():
    assert _load("/api/KitsuruDev?theme=onyx") == ("kitsurudev", "composite")
    assert _load("/api?username=tuxKOH&show_icons=true") == ("tuxkoh", "stats")
    assert _load("/api/top-langs?username=Artyomkun") == ("artyomkun", "top-langs")
    assert _load("/?username=ShayManor") == ("shaymanor", "stats")
    assert _load("/api/octocat/impact.svg") == ("octocat", "impact")
    assert _load("/api/streak/SheidY1") == ("sheidy1", "streak")


def test_embed_load_needs_githubs_image_proxy():
    assert analytics.embed_load(_line("gh-stats.com", "/api/env")) is None          # a browser/scanner
    assert _load("/api/octocat", status=404) is None
    assert analytics.embed_load(_line("gpufindr.com", "/api/octocat", ua=CAMO)) is None
    assert _load("/api/a/b/c") is None
    assert _load("/api/.env") is None                                            # not a GitHub name
    assert analytics.embed_load("not json") is None


def test_log_ingest_also_stores_web_hits_and_embed_loads(session, tmp_path):
    p = tmp_path / "access.log"
    p.write_text(_line("gpufindr.com", "/", ts=5e9) + "\n" + _line("gh-stats.com", "/api/x1", ts=5e9, ua=CAMO) + "\n")
    log_ingest.ingest_once(session, str(p))
    assert session.query(WebHit).filter_by(ts=5e9).count() == 1
    assert session.query(GhstatsLoad).filter_by(ts=5e9, username="x1").count() == 1


def test_backfill_web_reads_rolled_logs_once(session, tmp_path):
    live = tmp_path / "access.log"
    live.write_text(_line("gpufindr.com", "/", ts=10.0) + "\n")
    with gzip.open(tmp_path / "access-2026-01-01.log.gz", "wt") as f:
        f.write(_line("gpufindr.com", "/", ts=5.0) + "\n" + _line("pantheos.app", "/", ts=6.0) + "\n"
                + _line("gh-stats.com", "/api/x1", ts=7.0, ua=CAMO) + "\n")
    assert analytics.backfill_web(session, str(live)) == 3
    assert analytics.backfill_web(session, str(live)) == 0      # older than what's stored → skipped


def _ghstats_dir(tmp_path):
    s = sqlite3.connect(tmp_path / "settings.db")
    s.execute("CREATE TABLE users (username TEXT, github_id INTEGER, enrolled_at TEXT)")
    s.executemany("INSERT INTO users VALUES (?,?,?)",
                  [("newbie", 7, "2026-01-01T00:00:00Z"), ("octocat", None, "2026-01-01T00:00:00Z")])
    s.commit(); s.close()
    return str(tmp_path)


def test_sync_ghstats_mirrors_users(session, tmp_path):
    d = _ghstats_dir(tmp_path)
    assert analytics.sync_ghstats(session, d) == 1                          # newbie is new
    assert session.get(GhstatsUser, "newbie").oauth is True
    assert session.get(GhstatsUser, "octocat").oauth is False                # existing row updated
    assert analytics.sync_ghstats(session, d) == 0
    assert analytics.sync_ghstats(session, str(tmp_path / "missing")) == 0


# ---------------------------------------------------------------- reports

def test_ghstats_report_shape(client):
    r = client.get("/api/analytics/ghstats?range=30d").get_json()
    assert r["now"] == "2026-11-10"
    labels = [t["label"] for t in r["tiles"]]
    assert labels == ["Embedding users", "Live embeds", "Avg time on site", "Embed loads / day"]
    assert len(r["history"]) == 30 and len(r["hourly"]) == 24 and len(r["weekly"]) == 7
    assert 0 <= r["sessions"]["bounce"] <= 100 and len(r["sessions"]["hist"]) == 6
    assert r["hourly"][-1]["h"] == "15:00"
    statuses = {u["status"] for u in r["users"]}
    assert statuses == {"live", "stopped", "none"}
    assert [u["status"] for u in r["users"] if u["id"] == "kentcdodds"] == ["none"]   # enrolled, never fetched by camo
    live = sum(u["status"] == "live" for u in r["users"])
    assert r["tiles"][1]["v"] == live
    assert any(u["site_s"] > 0 for u in r["users"])                         # visitor → username link
    assert sum(b["v"] for b in r["lifetime"]) == sum(u["status"] != "none" for u in r["users"])


def test_ghstats_report_ranges(client):
    all_ = client.get("/api/analytics/ghstats?range=all").get_json()
    week = client.get("/api/analytics/ghstats?range=7d").get_json()
    assert len(all_["history"]) > len(week["history"]) == 7
    assert all_["tiles"][0]["v"] >= week["tiles"][0]["v"]


def test_ghstats_embedder_not_enrolled_and_no_site_traffic(session):
    session.query(WebHit).delete()
    session.add(GhstatsLoad(ts=ANALYTICS_NOW, username="legacy-user", widget="stats"))
    session.commit()
    r = analytics.ghstats_report(session, 7)
    row = next(u for u in r["users"] if u["id"] == "legacy-user")
    assert (row["status"], row["oauth"]) == ("live", False) and r["tiles"][2]["v"] == 0
    assert analytics.ghstats_user(session, "legacy-user")["enrolled"] is None


def test_reports_empty(session):
    for m in (GhstatsLoad, WebHit):
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


def test_history_is_null_before_tracking_and_live_needs_a_full_window(client):
    r = client.get("/api/analytics/ghstats?range=30d").get_json()
    assert r["tracked_from"] == "2026-10-21"
    before = [h for h in r["history"] if h["d"] < r["tracked_from"]]
    assert before and all(h["users"] is None and h["live"] is None for h in before)
    first = next(h for h in r["history"] if h["d"] == r["tracked_from"])
    assert first["users"] > 0 and first["live"] is None                        # 7-day window not full yet
    assert r["history"][-1]["live"] == r["tiles"][1]["v"]
    assert all(w["w"] >= "2026-10-19" for w in r["embeds"])                     # no untracked weeks
    assert r["embeds"][0]["started"] == 0                                       # first-week embedders aren't "started"
    assert any(u["since_tracking"] for u in r["users"]) and not all(u["since_tracking"] for u in r["users"])


def test_never_embedded_user_detail(session):
    u = analytics.ghstats_user(session, "kentcdodds")
    assert u["timeline"] == [] and u["enrolled"] == "2026-05-01"
