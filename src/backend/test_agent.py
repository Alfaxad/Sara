"""
Tests for the Sara Agent Core.

Written first following TDD approach.
Tests the hybrid ADK agent that orchestrates Sara's multi-turn workflow with event streaming.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from src.backend.agent import SaraAgent, AgentEvent, MAX_ROUNDS


class TestAgentEvent:
    """Tests for the AgentEvent dataclass."""

    def test_agent_event_thinking(self):
        """Test creating a thinking event."""
        event = AgentEvent(
            type="thinking",
            content="Let me search for the patient...",
            timestamp=1234567890.0
        )
        assert event.type == "thinking"
        assert event.content == "Let me search for the patient..."
        assert event.tool == ""
        assert event.result is None
        assert event.timestamp == 1234567890.0

    def test_agent_event_tool_call(self):
        """Test creating a tool_call event."""
        event = AgentEvent(
            type="tool_call",
            tool="GET",
            result={"resourceType": "Patient", "id": "123"},
            timestamp=1234567890.0
        )
        assert event.type == "tool_call"
        assert event.tool == "GET"
        assert event.result["resourceType"] == "Patient"

    def test_agent_event_complete(self):
        """Test creating a complete event."""
        event = AgentEvent(
            type="complete",
            result="The patient has hypertension",
            timestamp=1234567890.0
        )
        assert event.type == "complete"
        assert event.result == "The patient has hypertension"

    def test_agent_event_error(self):
        """Test creating an error event."""
        event = AgentEvent(
            type="error",
            content="Connection failed",
            timestamp=1234567890.0
        )
        assert event.type == "error"
        assert event.content == "Connection failed"


class TestSaraAgentInit:
    """Tests for SaraAgent initialization."""

    def test_agent_init(self):
        """Test agent initializes with correct URLs and functions."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )
        assert agent.sara_url == "http://localhost:8000"
        assert agent.fhir_url == "http://localhost:8080"
        assert agent.functions == functions


class TestSaraAgentBuildPrompt:
    """Tests for prompt building."""

    def test_build_prompt(self):
        """Test building MedAgentBench-style prompt."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        prompt = agent._build_prompt(
            context="Patient John Smith, DOB 1990-01-01",
            question="What is the patient's blood pressure?"
        )

        # Check prompt contains required elements
        assert "FHIR" in prompt
        assert "GET" in prompt
        assert "POST" in prompt
        assert "FINISH" in prompt
        assert "Patient John Smith" in prompt
        assert "blood pressure" in prompt
        assert "Patient_search" in prompt


class TestSaraAgentRun:
    """Tests for the main run() method."""

    @pytest.mark.asyncio
    async def test_run_completes_on_finish(self):
        """Test agent completes when Sara outputs FINISH."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        # Mock Sara to return FINISH immediately
        with patch.object(agent, '_call_sara', new_callable=AsyncMock) as mock_sara:
            mock_sara.return_value = 'FINISH(["The answer is 42"])'

            events: List[AgentEvent] = []
            async for event in agent.run(
                context="Test context",
                question="Test question"
            ):
                events.append(event)

        # Should have thinking event and complete event
        assert len(events) == 2
        assert events[0].type == "thinking"
        assert events[0].content == 'FINISH(["The answer is 42"])'
        assert events[1].type == "complete"
        assert events[1].result == "The answer is 42"

    @pytest.mark.asyncio
    async def test_run_executes_get_then_finish(self):
        """Test agent executes GET, gets result, then FINISH."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        # Mock Sara to return GET first, then FINISH
        call_count = 0

        async def mock_sara_response(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "GET http://localhost:8080/fhir/Patient?family=Smith"
            else:
                return 'FINISH(["Patient found: John Smith"])'

        # Mock FHIR client
        mock_fhir_result = MagicMock()
        mock_fhir_result.success = True
        mock_fhir_result.status_code = 200
        mock_fhir_result.data = {"resourceType": "Patient", "id": "123", "name": [{"family": "Smith"}]}
        mock_fhir_result.error = ""

        with patch.object(agent, '_call_sara', side_effect=mock_sara_response):
            with patch('modal.agent.FHIRClient') as mock_fhir_class:
                mock_fhir_instance = AsyncMock()
                mock_fhir_instance.execute = AsyncMock(return_value=mock_fhir_result)
                mock_fhir_instance.close = AsyncMock()
                mock_fhir_class.return_value = mock_fhir_instance

                events: List[AgentEvent] = []
                async for event in agent.run(
                    context="Test context",
                    question="Find patient Smith"
                ):
                    events.append(event)

        # Should have: thinking (GET), tool_call, thinking (FINISH), complete
        assert len(events) == 4
        assert events[0].type == "thinking"
        assert "GET" in events[0].content
        assert events[1].type == "tool_call"
        assert events[1].tool == "GET"
        assert events[2].type == "thinking"
        assert "FINISH" in events[2].content
        assert events[3].type == "complete"
        assert events[3].result == "Patient found: John Smith"

    @pytest.mark.asyncio
    async def test_run_stops_at_max_rounds(self):
        """Test agent stops at MAX_ROUNDS if no FINISH."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        # Mock Sara to always return GET (never finish)
        async def mock_sara_response(messages):
            return "GET http://localhost:8080/fhir/Patient?family=Smith"

        # Mock FHIR client
        mock_fhir_result = MagicMock()
        mock_fhir_result.success = True
        mock_fhir_result.status_code = 200
        mock_fhir_result.data = {"resourceType": "Bundle", "entry": []}
        mock_fhir_result.error = ""

        with patch.object(agent, '_call_sara', side_effect=mock_sara_response):
            with patch('modal.agent.FHIRClient') as mock_fhir_class:
                mock_fhir_instance = AsyncMock()
                mock_fhir_instance.execute = AsyncMock(return_value=mock_fhir_result)
                mock_fhir_instance.close = AsyncMock()
                mock_fhir_class.return_value = mock_fhir_instance

                events: List[AgentEvent] = []
                async for event in agent.run(
                    context="Test context",
                    question="Find patient Smith"
                ):
                    events.append(event)

        # Should have MAX_ROUNDS * 2 events (thinking + tool_call each round) + 1 error
        # Each round: thinking, tool_call
        # Final: error (max rounds reached)
        expected_events = MAX_ROUNDS * 2 + 1
        assert len(events) == expected_events
        assert events[-1].type == "error"
        assert "max" in events[-1].content.lower() or "round" in events[-1].content.lower()


class TestSaraAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_fhir_error_yields_error_event(self):
        """Test FHIR call failure yields error event but continues."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        call_count = 0

        async def mock_sara_response(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "GET http://localhost:8080/fhir/Patient?family=Smith"
            else:
                return 'FINISH(["Could not find patient"])'

        # Mock FHIR client to return error
        mock_fhir_result = MagicMock()
        mock_fhir_result.success = False
        mock_fhir_result.status_code = 500
        mock_fhir_result.data = {}
        mock_fhir_result.error = "Internal Server Error"

        with patch.object(agent, '_call_sara', side_effect=mock_sara_response):
            with patch('modal.agent.FHIRClient') as mock_fhir_class:
                mock_fhir_instance = AsyncMock()
                mock_fhir_instance.execute = AsyncMock(return_value=mock_fhir_result)
                mock_fhir_instance.close = AsyncMock()
                mock_fhir_class.return_value = mock_fhir_instance

                events: List[AgentEvent] = []
                async for event in agent.run(
                    context="Test context",
                    question="Find patient Smith"
                ):
                    events.append(event)

        # Should have: thinking, tool_call (with error in result), thinking, complete
        assert len(events) == 4
        assert events[1].type == "tool_call"
        # The error should be in the result
        assert events[1].result is not None

    @pytest.mark.asyncio
    async def test_sara_model_error_yields_error_event(self):
        """Test Sara model failure yields error event."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        # Mock Sara to raise exception
        with patch.object(agent, '_call_sara', new_callable=AsyncMock) as mock_sara:
            mock_sara.side_effect = Exception("Connection refused")

            events: List[AgentEvent] = []
            async for event in agent.run(
                context="Test context",
                question="Find patient Smith"
            ):
                events.append(event)

        # Should have error event
        assert len(events) == 1
        assert events[0].type == "error"
        assert "Connection refused" in events[0].content or "error" in events[0].content.lower()

    @pytest.mark.asyncio
    async def test_unknown_action_handled_gracefully(self):
        """Test UNKNOWN action type is handled gracefully."""
        functions = [{"name": "Patient_search", "description": "Search patients"}]
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        call_count = 0

        async def mock_sara_response(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "I'm not sure what to do..."  # UNKNOWN action
            else:
                return 'FINISH(["Unable to complete"])'

        with patch.object(agent, '_call_sara', side_effect=mock_sara_response):
            events: List[AgentEvent] = []
            async for event in agent.run(
                context="Test context",
                question="Find patient Smith"
            ):
                events.append(event)

        # Should continue despite UNKNOWN action
        # Events: thinking (unknown), error/tool_call for unknown, thinking (finish), complete
        assert any(e.type == "complete" for e in events)


class TestSaraAgentFormatFHIRResult:
    """Tests for FHIR result formatting."""

    def test_format_fhir_result_success(self):
        """Test formatting successful FHIR result."""
        functions = []
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        from src.backend.utils.fhir_client import FHIRResult

        result = FHIRResult(
            success=True,
            status_code=200,
            data={"resourceType": "Patient", "id": "123"}
        )

        formatted = agent._format_fhir_result(result)

        assert "Patient" in formatted
        assert "123" in formatted

    def test_format_fhir_result_error(self):
        """Test formatting FHIR error result."""
        functions = []
        agent = SaraAgent(
            sara_url="http://localhost:8000",
            fhir_url="http://localhost:8080",
            functions=functions
        )

        from src.backend.utils.fhir_client import FHIRResult

        result = FHIRResult(
            success=False,
            status_code=404,
            data={},
            error="Not Found"
        )

        formatted = agent._format_fhir_result(result)

        assert "error" in formatted.lower() or "not found" in formatted.lower() or "404" in formatted


class TestMaxRoundsConstant:
    """Test that MAX_ROUNDS constant is correct."""

    def test_max_rounds_is_8(self):
        """MAX_ROUNDS should be 8 as per design doc."""
        assert MAX_ROUNDS == 8
