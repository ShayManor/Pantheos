"""Load the agent's real skill files (markdown + frontmatter) from skills/."""
import os
import re

_DIR = os.path.join(os.path.dirname(__file__), "skills")
# ``name`` reaches load_skill from an agent-controlled MCP argument; restrict it
# to a bare slug so it can never traverse out of _DIR.
_SAFE_NAME = re.compile(r"[a-zA-Z0-9_-]+")


def _parse(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
        body = body.lstrip("\n")
    return meta, body


def _files():
    return sorted(f for f in os.listdir(_DIR) if f.endswith(".md"))


def list_skills():
    out = []
    for fname in _files():
        meta, _ = _parse(os.path.join(_DIR, fname))
        out.append({"name": meta.get("name", fname[:-3]),
                    "trigger": meta.get("trigger", ""),
                    "description": meta.get("description", "")})
    return out


def load_skill(name):
    if not _SAFE_NAME.fullmatch(name or ""):
        return {"error": "unknown skill", "name": name}
    path = os.path.join(_DIR, f"{name}.md")
    if not os.path.isfile(path):
        return {"error": "unknown skill", "name": name}
    meta, body = _parse(path)
    return {"name": meta.get("name", name), "trigger": meta.get("trigger", ""),
            "desc": meta.get("description", ""), "body": body}
