from app import acp_mock


def _collect(text, hsid=None):
    return list(acp_mock.run_turn(text, hsid))


def test_mock_stream_shape_is_deterministic():
    a = _collect("what is due this week")
    b = _collect("what is due this week")
    assert a == b  # no randomness / clock

    types = [e["type"] for e in a]
    assert types[0] == "reasoning"
    assert "text" in types
    assert types[-1] == "done"

    text = "".join(e["delta"] for e in a if e["type"] == "text")
    reasoning = "".join(e["delta"] for e in a if e["type"] == "reasoning")
    done = a[-1]
    assert done["text"] == text and done["reasoning"] == reasoning
    # tools surfaced both as events and in the final summary
    tool_names = [e["name"] for e in a if e["type"] == "tool"]
    assert done["tools"] == tool_names == ["calendar", "brightspace", "queue"]
    # markdown + latex + a ticket ref are present so the UI has something to render
    assert "$" in text and "`" in text and "GRD-0182" in text


def test_mock_preserves_or_mints_session_id():
    assert _collect("hi", "hs-keep")[-1]["hermes_session_id"] == "hs-keep"
    assert _collect("hi", None)[-1]["hermes_session_id"] == "mock-session"
