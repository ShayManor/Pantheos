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
