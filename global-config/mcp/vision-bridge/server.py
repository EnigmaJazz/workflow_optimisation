#!/usr/bin/env python3
"""Vision bridge MCP server — lets text-only models analyze images.

Exposes one tool, `describe_image(path, question)`, which sends the image to a
vision-capable model and returns a text description the calling model can
reason about.

Backend chain (first usable answer wins; empty content or transport failure
falls through):
  1. gpt-5.6-luna via the opencode-go proxy  (AI-SDK image+media format —
     image_url returns an empty 200 for luna on zen)
  2. gpt-5.6-luna via api.openai.com directly (OpenAI image_url format, OAuth
     token from opencode's auth.json)
  3. qwen3.6-plus via the opencode-go proxy  (image_url format)

Stdio transport: newline-delimited JSON-RPC 2.0 (MCP spec).
Zero dependencies: Python 3 stdlib only.
"""

import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

PROXY_URL = os.environ.get(
    "VISION_BRIDGE_URL",
    "http://127.0.0.1:8788/v1/chat/completions",
)
PROXY_MODEL = os.environ.get("VISION_BRIDGE_MODEL", "gpt-5.6-luna")
FALLBACK_MODEL = os.environ.get("VISION_BRIDGE_FALLBACK_MODEL", "qwen3.6-plus")
OPENAI_URL = os.environ.get(
    "VISION_BRIDGE_OPENAI_URL",
    "https://api.openai.com/v1/chat/completions",
)
OPENAI_MODEL = os.environ.get("VISION_BRIDGE_OPENAI_MODEL", "gpt-5.6-luna")
AUTH_FILE = os.environ.get(
    "VISION_BRIDGE_AUTH_FILE",
    os.path.expanduser("~/.local/share/opencode/auth.json"),
)
TIMEOUT = int(os.environ.get("VISION_BRIDGE_TIMEOUT", "120"))
UA = "curl/8.5.0"  # the go proxy sits behind Cloudflare; urllib's default UA is 403'd

LEG_LOG = os.environ.get(
    "VISION_BRIDGE_LEG_LOG",
    os.path.expanduser("~/.local/share/vision-bridge/leg.log"),
)

TOOL_DESCRIPTION = (
    "Analyze an image file (screenshot, mockup, UI render) with a vision model "
    "and return a detailed text description. Use this when you need to "
    "understand visual output (rendered UI, screenshots, design references) "
    "but your own model cannot process images. Returns layout, colors, text, "
    "spacing, and any issues relevant to the question."
)


def _mime_for(path):
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    if mime == "application/octet-stream":
        mime = "image/png"  # unknown extension: assume an image
    return mime


def _post(url, headers, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        return None, f"HTTP {exc.code}: {detail}"
    except Exception as exc:  # noqa: BLE001 - surface any transport failure
        return None, f"transport: {exc}"


def _content_of(body):
    """Extract non-empty assistant content; None on empty/absent (fallback trigger)."""
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    return content if isinstance(content, str) and content.strip() else None


# Models occasionally answer politely that they cannot see the attached image
# (e.g. luna on zen: "Please upload the image..."). That is a failure of the
# vision leg, not an answer — treat it as a fallback trigger. "can't see" only
# counts as a refusal when it refers to an image/photo/picture (a model that
# saw the image may say "can't see the exact quantity clearly" — legit answer).
_REFUSAL_PATTERNS = (
    "please upload",
    "upload the image",
    "upload an image",
    "no image was",
    "no image is",
    "no image provided",
    "no image attached",
    "no image with",
    "no photo",
    "no picture",
    "did not receive",
    "didn't receive",
    "don't see an image",
    "do not see an image",
    "cannot view the image",
)

import re as _re

_REFUSAL_RE = _re.compile(
    r"(?:can't|cannot|couldn't|could not|unable to) "
    r"(?:see|view) (?:the|any|an|a|this|that) (?:image|photo|picture)"
)


def _is_vision_refusal(text):
    lower = text.lower()
    return _REFUSAL_RE.search(lower) is not None or any(
        p in lower for p in _REFUSAL_PATTERNS
    )


def _openai_credentials():
    """Return (access_token, chatgpt_account_id) for the openai leg, or (None, None)."""
    try:
        with open(AUTH_FILE) as fh:
            auth = json.load(fh)
        tok = (auth.get("openai") or {}).get("access")
        if not tok:
            return None, None
        acct = None
        try:
            payload = tok.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            acct = (claims.get("https://api.openai.com/auth") or {}).get(
                "chatgpt_account_id"
            )
        except Exception:  # noqa: BLE001 - token not a JWT; header omitted
            pass
        return tok, acct
    except Exception:  # noqa: BLE001 - no auth file
        return None, None


def _backend_luna_proxy(img_b64, mime, question):
    """Leg 1: gpt-5.6-luna via opencode-go proxy — AI-SDK image+media format."""
    payload = {
        "model": PROXY_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                        or "Describe this image in detail: layout, colors, "
                        "text, spacing, and anything visually notable.",
                    },
                    {
                        "type": "image",
                        "media": {"type": mime, "data": img_b64},
                    },
                ],
            }
        ],
    }
    return _post(
        PROXY_URL,
        {"Content-Type": "application/json", "User-Agent": UA},
        payload,
    )


def _backend_luna_openai(img_b64, mime, question):
    """Leg 2: gpt-5.6-luna via api.openai.com — OpenAI image_url format."""
    tok, acct = _openai_credentials()
    if not tok:
        return None, "no openai token in auth file"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tok}",
        "User-Agent": UA,
    }
    if acct:
        headers["OpenAI-ChatGPT-Account-Id"] = acct
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                        or "Describe this image in detail: layout, colors, "
                        "text, spacing, and anything visually notable.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_b64}",
                        },
                    },
                ],
            }
        ],
    }
    return _post(OPENAI_URL, headers, payload)


def _backend_qwen_proxy(img_b64, mime, question):
    """Leg 3: qwen3.6-plus via opencode-go proxy — image_url format."""
    payload = {
        "model": FALLBACK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                        or "Describe this image in detail: layout, colors, "
                        "text, spacing, and anything visually notable.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_b64}",
                        },
                    },
                ],
            }
        ],
    }
    return _post(
        PROXY_URL,
        {"Content-Type": "application/json", "User-Agent": UA},
        payload,
    )


BACKENDS = [
    ("gpt-5.6-luna via opencode-go", _backend_luna_proxy),
    ("gpt-5.6-luna via openai", _backend_luna_openai),
    ("qwen3.6-plus via opencode-go", _backend_qwen_proxy),
]


def _describe(path, question):
    with open(path, "rb") as fh:
        img_b64 = base64.b64encode(fh.read()).decode("ascii")
    mime = _mime_for(path)
    errors = []
    started = time.time()
    used = None
    for name, backend in BACKENDS:
        body, err = backend(img_b64, mime, question)
        if err is not None:
            errors.append(f"{name}: {err}")
            continue
        content = _content_of(body)
        if content is not None and not _is_vision_refusal(content):
            used = name
            break
        errors.append(f"{name}: empty response" if content is None
                      else f"{name}: vision refusal")
    duration = round(time.time() - started, 1)
    if used is not None:
        _log_leg(used, path, duration)
        return content
    _log_leg("none", path, duration)
    return "All vision backends failed: " + " | ".join(errors)


def _log_leg(leg, path, duration):
    """Append one line per answered call so provenance is auditable."""
    try:
        os.makedirs(os.path.dirname(LEG_LOG), exist_ok=True)
        with open(LEG_LOG, "a") as fh:
            fh.write(
                f'{time.strftime("%Y-%m-%d %H:%M:%S")} '
                f'leg={leg} duration={duration}s path={path}\n'
            )
    except Exception:  # noqa: BLE001 - logging must never break the call
        pass


def _tool_result(text):
    return {
        "content": [{"type": "text", "text": text}],
        "isError": False,
    }


def _handle_request(msg):
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "vision-bridge", "version": "0.2.0"},
            },
        }
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "tools": [
                    {
                        "name": "describe_image",
                        "description": TOOL_DESCRIPTION,
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": (
                                        "Absolute path to the image file "
                                        "(png/jpg/webp)."
                                    ),
                                },
                                "question": {
                                    "type": "string",
                                    "description": (
                                        "What to look for. Defaults to a "
                                        "general detailed description."
                                    ),
                                },
                            },
                            "required": ["path"],
                        },
                    }
                ]
            },
        }
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        if name != "describe_image":
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "content": [
                        {"type": "text", "text": f"Unknown tool: {name}"}
                    ],
                    "isError": True,
                },
            }
        path = args.get("path", "")
        try:
            text = _describe(path, args.get("question", ""))
        except FileNotFoundError:
            text = f"Image not found: {path}"
        except IsADirectoryError:
            text = f"Path is a directory, not an image: {path}"
        except Exception as exc:  # noqa: BLE001
            text = f"Failed to read image: {exc}"
        return {"jsonrpc": "2.0", "id": mid, "result": _tool_result(text)}
    return {
        "jsonrpc": "2.0",
        "id": mid,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle_request(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
