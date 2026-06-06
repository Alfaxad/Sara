"""
Tests for Sara action parser.
Written first following TDD approach.
"""

import pytest
from src.backend.utils.parser import ActionType, Action, extract_action, parse_action


class TestParseGetSimple:
    """Test GET requests with a single parameter."""

    def test_parse_get_simple(self):
        """GET with one param extracts endpoint and params correctly."""
        content = "GET http://localhost:8080/fhir/Patient?family=Smith"

        action = parse_action(content)

        assert action.type == ActionType.GET
        assert action.endpoint == "/fhir/Patient"
        assert action.params == {"family": "Smith"}
        assert action.body == {}
        assert action.answer == ""
        assert action.raw_content == ""


class TestParseGetMultipleParams:
    """Test GET requests with multiple parameters."""

    def test_parse_get_multiple_params(self):
        """GET with multiple params extracts all params correctly."""
        content = "GET http://localhost:8080/fhir/Patient?family=Smith&given=John&birthdate=1990-01-01"

        action = parse_action(content)

        assert action.type == ActionType.GET
        assert action.endpoint == "/fhir/Patient"
        assert action.params == {
            "family": "Smith",
            "given": "John",
            "birthdate": "1990-01-01"
        }

    def test_parse_get_no_params(self):
        """GET without params still works."""
        content = "GET http://localhost:8080/fhir/Patient/123"

        action = parse_action(content)

        assert action.type == ActionType.GET
        assert action.endpoint == "/fhir/Patient/123"
        assert action.params == {}


class TestParsePostWithBody:
    """Test POST requests with JSON body."""

    def test_parse_post_with_body(self):
        """POST with JSON body extracts endpoint and body correctly."""
        content = '''POST http://localhost:8080/fhir/Observation
{
    "resourceType": "Observation",
    "status": "final",
    "code": {
        "coding": [{"system": "http://loinc.org", "code": "8867-4"}]
    },
    "valueQuantity": {"value": 72, "unit": "bpm"}
}'''

        action = parse_action(content)

        assert action.type == ActionType.POST
        assert action.endpoint == "/fhir/Observation"
        assert action.body["resourceType"] == "Observation"
        assert action.body["status"] == "final"
        assert action.body["valueQuantity"]["value"] == 72
        assert action.params == {}

    def test_parse_post_simple_body(self):
        """POST with simple JSON body."""
        content = '''POST http://localhost:8080/fhir/Patient
{"resourceType": "Patient", "name": [{"family": "Doe"}]}'''

        action = parse_action(content)

        assert action.type == ActionType.POST
        assert action.endpoint == "/fhir/Patient"
        assert action.body["resourceType"] == "Patient"
        assert action.body["name"][0]["family"] == "Doe"


class TestParseFinishSimple:
    """Test FINISH actions with simple answers."""

    def test_parse_finish_simple(self):
        """FINISH with simple answer extracts correctly."""
        content = 'FINISH(["42"])'

        action = parse_action(content)

        assert action.type == ActionType.FINISH
        assert action.answer == "42"
        assert action.endpoint == ""
        assert action.params == {}
        assert action.body == {}

    def test_parse_finish_text_answer(self):
        """FINISH with text answer."""
        content = 'FINISH(["The patient has hypertension"])'

        action = parse_action(content)

        assert action.type == ActionType.FINISH
        assert action.answer == "The patient has hypertension"

    def test_parse_finish_empty_array(self):
        """FINISH([]) is valid and means no answer/action needed."""
        action = parse_action("FINISH([])")

        assert action.type == ActionType.FINISH
        assert action.answer == ""

    def test_parse_finish_numeric_answer(self):
        """FINISH with a numeric value returns a stringified value."""
        action = parse_action("FINISH([125.5])")

        assert action.type == ActionType.FINISH
        assert action.answer == "125.5"

    def test_parse_finish_multiple_values(self):
        """FINISH with multiple values preserves JSON array semantics."""
        action = parse_action('FINISH([6.5, "2022-10-15T08:30:00+00:00"])')

        assert action.type == ActionType.FINISH
        assert action.answer == '[6.5, "2022-10-15T08:30:00+00:00"]'

    def test_parse_finish_unquoted_identifier(self):
        """Some benchmark answers are unquoted identifiers like MRNs."""
        action = parse_action("FINISH([S1234567])")

        assert action.type == ActionType.FINISH
        assert action.answer == "S1234567"


class TestParseFinishWithReasoning:
    """Test FINISH actions that have reasoning text before them."""

    def test_parse_finish_with_reasoning(self):
        """Text before FINISH is ignored, answer is extracted."""
        content = '''Based on my analysis of the patient records, I found that the
patient's blood pressure readings indicate hypertension. The systolic values
consistently exceed 140 mmHg.

FINISH(["hypertension"])'''

        action = parse_action(content)

        assert action.type == ActionType.FINISH
        assert action.answer == "hypertension"

    def test_parse_finish_with_inline_reasoning(self):
        """Reasoning on same line before FINISH."""
        content = 'After reviewing the data, FINISH(["positive"])'

        action = parse_action(content)

        assert action.type == ActionType.FINISH
        assert action.answer == "positive"


class TestParseUnknown:
    """Test that random/invalid text returns UNKNOWN."""

    def test_parse_unknown(self):
        """Random text returns UNKNOWN action with raw content."""
        content = "I'm not sure what to do next. Let me think about this..."

        action = parse_action(content)

        assert action.type == ActionType.UNKNOWN
        assert action.raw_content == content
        assert action.endpoint == ""
        assert action.params == {}
        assert action.body == {}
        assert action.answer == ""

    def test_parse_empty_string(self):
        """Empty string returns UNKNOWN."""
        content = ""

        action = parse_action(content)

        assert action.type == ActionType.UNKNOWN
        assert action.raw_content == ""

    def test_parse_partial_get(self):
        """Malformed GET returns UNKNOWN."""
        content = "GET without a url"

        action = parse_action(content)

        assert action.type == ActionType.UNKNOWN

    def test_parse_partial_post(self):
        """POST without body returns UNKNOWN."""
        content = "POST http://localhost:8080/fhir/Patient"

        action = parse_action(content)

        assert action.type == ActionType.UNKNOWN


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_get_with_encoded_params(self):
        """GET with URL-encoded params are decoded."""
        content = "GET http://localhost:8080/fhir/Patient?name=John%20Doe"

        action = parse_action(content)

        assert action.type == ActionType.GET
        # URL-encoded params are decoded automatically
        assert action.params == {"name": "John Doe"}

    def test_post_with_invalid_json(self):
        """POST with invalid JSON returns UNKNOWN."""
        content = '''POST http://localhost:8080/fhir/Patient
{invalid json here}'''

        action = parse_action(content)

        assert action.type == ActionType.UNKNOWN

    def test_finish_with_multiple_answers(self):
        """FINISH with multiple items preserves the whole JSON array."""
        content = 'FINISH(["answer1", "answer2"])'

        action = parse_action(content)

        assert action.type == ActionType.FINISH
        assert action.answer == '["answer1", "answer2"]'

    def test_case_sensitivity(self):
        """Action keywords should be case-sensitive."""
        content = "get http://localhost:8080/fhir/Patient?id=1"

        action = parse_action(content)

        # lowercase 'get' should not match
        assert action.type == ActionType.UNKNOWN


class TestExtractAction:
    """Test extraction from verbose or fenced model output."""

    def test_extract_code_fenced_get(self):
        raw = "```tool_code\nGET http://localhost:8080/fhir/Patient?family=Smith\n```"

        assert extract_action(raw) == "GET http://localhost:8080/fhir/Patient?family=Smith"

    def test_extract_finish_from_verbose_text(self):
        raw = "I checked the chart.\nFINISH([42])"

        assert extract_action(raw) == "FINISH([42])"

    def test_extract_complete_post_json(self):
        raw = '''I will create the order.
POST http://localhost:8080/fhir/ServiceRequest
{"resourceType":"ServiceRequest","status":"active"}
extra text'''

        assert extract_action(raw) == (
            'POST http://localhost:8080/fhir/ServiceRequest\n'
            '{"resourceType":"ServiceRequest","status":"active"}'
        )
