"""Delphi's canned conversational replies.

The real agent runtime is out of scope; this keyword-routes a question to a
fixed answer + the tools it "used", mirroring the prototype's reply().
"""

_ROUTES = [
    (("due", "friday", "week"),
     "This week: GRD-0182 TMLR revisions (2d, P0), STA-0044 STAT 511 PS4 (3d, P1), "
     "EVC-0074 motor sync (4d, P1). The TMLR one is the only P0 with real slack risk — "
     "6h of work, 2 days out. I'd start it today.",
     ["calendar", "brightspace", "queue"]),
    (("merlin", "rubik"),
     "MERLIN is nominal. 2 open tickets: MER-0093 (Rubik Pi port), blocked-ish on "
     "MER-0088 (INT8 quant, backburner). Both onboard containers are LOS — the Jetson's "
     "been off ~3h, expected, not an incident.",
     ["queue", "vm"]),
    (("gh-stats", "500", "canary"),
     "Alert at t-11m: 5XX hit 6.1% on gh-stats-api. I traced a cold-cache null-deref in "
     "the rate-limit middleware, added a guard + fallback, and opened the fix under "
     "GHS-0311. Canary 5XX back to 0.3%, waiting on your merge.",
     ["vm", "github", "claude"]),
    (("rank", "queue"),
     "Re-ranked. Top: GHS-0311 (9.1, executing), GRD-0182 (9.4), EVC-0074 (6.8), "
     "STA-0044 (6.1). Nothing else moved.",
     ["queue"]),
]

_DEFAULT = (
    "I can pull ticket status, project health, run history, or metrics — or launch on "
    "any ticket. Try a suggestion, attach a file, or dictate.",
    [],
)


def reply(text):
    lower = (text or "").lower()
    for keywords, answer, tools in _ROUTES:
        if any(k in lower for k in keywords):
            return {"text": answer, "tools": tools}
    return {"text": _DEFAULT[0], "tools": _DEFAULT[1]}
