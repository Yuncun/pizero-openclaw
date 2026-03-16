import json
from typing import Generator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config

_http_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        _http_session.mount("http://", adapter)
        _http_session.mount("https://", adapter)
    return _http_session


def stream_response(
    user_text: str,
    history: list[dict] | None = None,
) -> Generator[str, None, None]:
    """Send user_text to OpenClaw /v1/chat/completions with streaming.

    Yields text deltas as they arrive via SSE.
    """
    url = f"{config.OPENCLAW_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENCLAW_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "x-openclaw-agent-id": config.OPENCLAW_AGENT_ID,
    }

    messages = []
    if history:
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_text})

    body = {
        "model": "openclaw",
        "stream": True,
        "messages": messages,
    }

    print(f"[openclaw] POST {url} (stream=true)")

    try:
        resp = _get_session().post(url, json=body, headers=headers, stream=True, timeout=(30, 120))
    except (requests.ConnectionError, requests.Timeout) as e:
        raise RuntimeError(f"Cannot reach OpenClaw at {config.OPENCLAW_BASE_URL}: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenClaw request failed ({resp.status_code}): {resp.text[:300]}"
        )

    buf = ""
    for chunk in resp.iter_content(chunk_size=512, decode_unicode=True):
        if chunk is None:
            continue
        buf += chunk
        while "\n" in buf or "\r" in buf:
            line, _, buf = buf.partition("\n")
            line = line.strip().rstrip("\r")
            if not line:
                continue
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if not data_str or data_str == "[DONE]":
                    return
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
