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

    Format: FINISH(["answer"]) or FINISH(["answer1", "answer2", ...])
    The FINISH can appear anywhere in the content (after reasoning text).
    """
    # Match FINISH with array of strings - takes first answer
    # Pattern matches FINISH(["..."]) or FINISH(["...", "...", ...])
    pattern = r'FINISH\(\[([^\]]+)\]\)'
    match = re.search(pattern, content)

    if not match:
        return None

    try:
        # Extract the array contents
        array_content = match.group(1)

        # Parse individual string values from the array
        # Match quoted strings (handles both single and double quotes)
        string_pattern = r'"([^"]*)"'
        strings = re.findall(string_pattern, array_content)

        if not strings:
            # Try single quotes
            string_pattern = r"'([^']*)'"
            strings = re.findall(string_pattern, array_content)

        if strings:
            # Take the first answer
            return Action(
                type=ActionType.FINISH,
                answer=strings[0]
            )
    except Exception:
        pass

    return None
