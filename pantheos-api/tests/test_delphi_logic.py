from app import delphi


def test_reply_routes():
    assert "calendar" in delphi.reply("what is due this week")["tools"]
    assert delphi.reply("status of merlin rubik")["tools"] == ["queue", "vm"]
    assert "github" in delphi.reply("did the gh-stats fix pass canary")["tools"]
    assert delphi.reply("re-rank my queue")["tools"] == ["queue"]


def test_reply_default_and_empty():
    assert delphi.reply("hello there")["tools"] == []
    assert delphi.reply("")["tools"] == []
    assert delphi.reply(None)["tools"] == []


def test_draft_ticket_routes():
    d = delphi.draft_ticket({"title": "port inference to rubik pi"})
    assert d["project_key"] == "merlin"
    assert d["pri"] in {0, 1, 2, 3}
    assert d["summary"]
    assert d["effort_hours"] > 0
    assert d["deadline_hours"] > 0
    assert "area_id" not in d                         # project route omits area
    assert delphi.draft_ticket({"summary": "canary 5XX on gh-stats"})["project_key"] == "ghstats"
    assert delphi.draft_ticket({"title": "STAT 511 problem set"})["area_id"] == "stat511"


def test_draft_ticket_default_keeps_attach():
    d = delphi.draft_ticket({"title": "wire up the thing", "project_key": "ghstats"})
    assert d["project_key"] == "ghstats"              # keeps the user's project
    assert "wire up the thing" in d["summary"]
    assert d["pri"] in {0, 1, 2, 3}
    d2 = delphi.draft_ticket({"title": "misc chore", "area_id": "side"})
    assert d2["area_id"] == "side"
    assert "project_key" not in d2


def test_draft_ticket_empty():
    d = delphi.draft_ticket({})
    assert d["title"]                                 # usable draft from nothing
    assert d["summary"]
    assert d["effort_hours"] > 0
    assert d["deadline_hours"] > 0
