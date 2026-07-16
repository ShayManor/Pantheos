"""End-to-end credential check for Delphi's external MCP connectors.

Hits each real service with its secret and confirms it authenticates. Read-only:
identity lookups where possible, one tiny search for Exa. No SDK deps — plain
urllib, same as app/openai_client.py.

Env (the GitHub Actions secrets):
  GH_PAT          GitHub personal access token
  HF_API_KEY      Hugging Face access token
  WANDB_API_KEY   Weights & Biases API key
  EXA_API_KEY     Exa API key

Exit code 0 iff every configured credential authenticated. A missing env var is
reported as SKIP (not a failure); a present-but-rejected key is FAIL.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

TIMEOUT = float(os.environ.get("VERIFY_TIMEOUT", "30"))


def _call(method, url, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    with resp:
        return resp.status, json.loads(resp.read().decode("utf-8") or "{}")


def check_github(key):
    status, data = _call("GET", "https://api.github.com/user", {
        "Authorization": f"Bearer {key}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pantheos-verify",
    })
    return f"authed as @{data.get('login')} (id {data.get('id')})"


def check_hf(key):
    status, data = _call("GET", "https://huggingface.co/api/whoami-v2",
                         {"Authorization": f"Bearer {key}"})
    scopes = (data.get("auth") or {}).get("accessToken", {}).get("role")
    return f"authed as {data.get('name')} ({data.get('type')}, role={scopes})"


def check_wandb(key):
    token = base64.b64encode(f"api:{key}".encode()).decode()
    status, data = _call("POST", "https://api.wandb.ai/graphql", {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "pantheos-verify",
    }, {"query": "{ viewer { username entity } }"})
    viewer = (data.get("data") or {}).get("viewer") or {}
    if not viewer.get("username"):
        raise RuntimeError(f"no viewer returned: {json.dumps(data)[:200]}")
    return f"authed as {viewer.get('username')} (entity {viewer.get('entity')})"


def check_exa(key):
    status, data = _call("POST", "https://api.exa.ai/search", {
        "x-api-key": key,
        "Content-Type": "application/json",
    }, {"query": "hello world", "numResults": 1})
    n = len(data.get("results") or [])
    return f"search ok ({n} result, requestId {data.get('requestId', '?')})"


CHECKS = [
    ("GitHub", "GH_PAT", check_github),
    ("Hugging Face", "HF_API_KEY", check_hf),
    ("Weights & Biases", "WANDB_API_KEY", check_wandb),
    ("Exa", "EXA_API_KEY", check_exa),
]


def main():
    failures, skipped = 0, 0
    print("Delphi connector credential check\n" + "=" * 40)
    for name, env, fn in CHECKS:
        key = os.environ.get(env)
        if not key:
            print(f"SKIP  {name:<18} {env} not set")
            skipped += 1
            continue
        try:
            detail = fn(key)
            print(f"PASS  {name:<18} {detail}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:200]
            print(f"FAIL  {name:<18} HTTP {exc.code}: {body}")
            failures += 1
        except Exception as exc:  # noqa: BLE001 - report any failure per-service
            print(f"FAIL  {name:<18} {type(exc).__name__}: {exc}")
            failures += 1
    print("=" * 40)
    print(f"{len(CHECKS) - failures - skipped} passed, {failures} failed, {skipped} skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
