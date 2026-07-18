from app.ticket_run import run_ticket


def _collect(gen):
    events = list(gen)
    types = [e["type"] for e in events]
    done = events[-1]
    return events, types, done


def test_run_ticket_event_sequence_and_tools():
    events, types, done = _collect(run_ticket("GRD-0182", "Fix flaky auth test", "Research", "propose"))
    # reasoning first, at least one tool, text chunks, done last
    assert types[0] == "reasoning"
    assert "tool" in types
    assert "text" in types
    assert types[-1] == "done"
    # tool names are TOOLMAP keys
    tool_names = [e["name"] for e in events if e["type"] == "tool"]
    assert tool_names and set(tool_names) <= {"github", "vm", "calendar", "brightspace", "queue", "claude"}
    assert done["tools"] == tool_names
    # streamed text reconstructs the final output
    streamed = "".join(e["delta"] for e in events if e["type"] == "text")
    assert streamed == done["text"]
    assert "GRD-0182" in done["reasoning"]


def test_run_ticket_is_deterministic():
    a = list(run_ticket("T-1", "Deploy the service", "Infra", "auto_pr"))
    b = list(run_ticket("T-1", "Deploy the service", "Infra", "auto_pr"))
    assert a == b


def test_run_ticket_autonomy_variants():
    propose = list(run_ticket("T-1", "x", "A", "propose"))[-1]
    autopr = list(run_ticket("T-1", "x", "A", "auto_pr"))[-1]
    full = list(run_ticket("T-1", "x", "A", "full"))[-1]
    assert "review" in propose["report"].lower()
    assert "auto-merge" in autopr["report"].lower()
    assert "live" in full["report"].lower()
    # unknown autonomy falls back to the propose/stop-for-review path
    unknown = list(run_ticket("T-1", "x", "A", None))[-1]
    assert "review" in unknown["report"].lower()


def test_run_ticket_keyword_routing_covers_all_routes():
    # each keyword family plus the default path
    assert "vm" in list(run_ticket("T", "latency alert on api", "A", "full"))[-1]["tools"]
    assert "queue" in list(run_ticket("T", "release rollout", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "update the readme", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "fix flaky ci test", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "something unrelated", "A", "full"))[-1]["tools"]
