"""
Sara Action Parser

Parses Sara's model output to determine what action to take:
- GET: Read from FHIR server
- POST: Write to FHIR server
- FINISH: Task complete with answer
- UNKNOWN: Unrecognized output format
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse


class ActionType(Enum):
    """Types of actions Sara can output."""
    GET = "GET"
    POST = "POST"
    FINISH = "FINISH"
    UNKNOWN = "UNKNOWN"


@dataclass
class Action:
    """Represents a parsed action from Sara's output."""
    type: ActionType
    endpoint: str = ""
    params: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    answer: str = ""
    raw_content: str = ""


def parse_action(content: str) -> Action:
    """
    Parse Sara's output and return the appropriate Action.

    Args:
        content: Raw string output from Sara model

    Returns:
        Action object with parsed type, endpoint, params, body, or answer

    Examples:
        >>> parse_action("GET http://localhost:8080/fhir/Patient?family=Smith")
        Action(type=ActionType.GET, endpoint="/fhir/Patient", params={"family": "Smith"}, ...)

        >>> parse_action('FINISH(["42"])')
        Action(type=ActionType.FINISH, answer="42", ...)
    """
    if not content:
        return Action(type=ActionType.UNKNOWN, raw_content=content)

    # Try to parse FINISH action (can appear anywhere in content)
    finish_action = _parse_finish(content)
    if finish_action:
        return finish_action

    # Try to parse GET action (must start with GET)
    get_action = _parse_get(content)
    if get_action:
        return get_action

    # Try to parse POST action (must start with POST)
    post_action = _parse_post(content)
    if post_action:
        return post_action

    # Unknown action type
    return Action(type=ActionType.UNKNOWN, raw_content=content)


def extract_action(raw: str) -> str:
    """
    Extract a clean GET/POST/FINISH action from a model response.

    Sara is trained to emit only an action, but provider wrappers and code-fence
    formatting sometimes add surrounding text. Keep this logic centralized so
    Modal, local tests, and IRIS integrations all parse the same way.
    """
    if not raw:
        return raw

    stripped = raw.strip().replace("```tool_code", "").replace("```", "").strip()

    if stripped.startswith("GET ") or stripped.startswith("POST ") or stripped.startswith("FINISH("):
        return stripped

    finish_match = re.search(r"FINISH\(\[.*?\]\)", stripped, re.DOTALL)
    if finish_match:
        return finish_match.group(0)

    get_match = re.search(r"^(GET\s+https?://\S+)", stripped, re.MULTILINE)
    if get_match:
        return get_match.group(1)

    post_match = re.search(r"^(POST\s+https?://\S+)\n(\{.*)", stripped, re.MULTILINE | re.DOTALL)
    if not post_match:
        return stripped

    url_line = post_match.group(1)
    rest = post_match.group(2)
    brace_count = 0
    end_idx = 0
    for i, char in enumerate(rest):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    if end_idx > 0:
        return f"{url_line}\n{rest[:end_idx]}"
    return stripped


def _parse_get(content: str) -> Action | None:
    """
    Parse a GET action from content.

    Format: GET http://localhost:8080/fhir/Resource?params
    """
    # Match GET followed by URL
    pattern = r'^GET\s+(https?://[^\s]+)'
    match = re.match(pattern, content.strip())

    if not match:
        return None

    url = match.group(1)

    try:
        parsed = urlparse(url)
        endpoint = parsed.path

        # Parse query parameters
        params = {}
        if parsed.query:
            # parse_qs returns lists, we want single values
            qs = parse_qs(parsed.query)
            params = {k: v[0] for k, v in qs.items()}

        return Action(
            type=ActionType.GET,
            endpoint=endpoint,
            params=params
        )
    except Exception:
        return None


def _parse_post(content: str) -> Action | None:
    """
    Parse a POST action from content.

    Format:
        POST http://localhost:8080/fhir/Resource
        {JSON body}
    """
    # Match POST followed by URL, then newline and JSON body
    pattern = r'^POST\s+(https?://[^\s]+)\s*\n(.+)'
    match = re.match(pattern, content.strip(), re.DOTALL)

    if not match:
        return None

    url = match.group(1)
    json_str = match.group(2).strip()

    try:
        parsed = urlparse(url)
        endpoint = parsed.path

        # Parse JSON body
        body = json.loads(json_str)

        return Action(
            type=ActionType.POST,
            endpoint=endpoint,
            body=body
        )
    except (json.JSONDecodeError, Exception):
        return None


def _parse_finish(content: str) -> Action | None:
    """
    Parse a FINISH action from content.

    Format: FINISH(["answer"]), FINISH([42]), FINISH([]), or
    FINISH([6.5, "2022-10-15T08:30:00+00:00"]).
    The FINISH can appear anywhere in the content.
    """
    pattern = r"FINISH\(\[(.*?)\]\)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    array_content = match.group(1).strip()
    if not array_content:
        return Action(type=ActionType.FINISH, answer="")

    try:
        parsed = json.loads(f"[{array_content}]")
    except json.JSONDecodeError:
        return Action(type=ActionType.FINISH, answer=array_content.strip())

    if len(parsed) == 0:
        answer = ""
    elif len(parsed) == 1:
        answer = str(parsed[0])
    else:
        answer = json.dumps(parsed)

    return Action(type=ActionType.FINISH, answer=answer)
