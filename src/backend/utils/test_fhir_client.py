"""
Tests for the async FHIR client.

Uses pytest-httpx for mocking HTTP requests.
"""

import pytest
from httpx import ConnectError

from src.backend.utils.fhir_client import FHIRClient, FHIRResult
from src.backend.utils.parser import Action, ActionType


class TestFHIRResult:
    """Tests for the FHIRResult dataclass."""

    def test_fhir_result_success(self):
        """Test creating a successful result."""
        result = FHIRResult(
            success=True,
            status_code=200,
            data={"resourceType": "Patient", "id": "123"}
        )
        assert result.success is True
        assert result.status_code == 200
        assert result.data["resourceType"] == "Patient"
        assert result.error == ""

    def test_fhir_result_error(self):
        """Test creating an error result."""
        result = FHIRResult(
            success=False,
            status_code=500,
            data={},
            error="Internal Server Error"
        )
        assert result.success is False
        assert result.status_code == 500
        assert result.error == "Internal Server Error"


class TestFHIRClientGet:
    """Tests for GET requests."""

    @pytest.mark.asyncio
    async def test_get_success(self, httpx_mock):
        """Test successful GET request."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient/123",
            json={"resourceType": "Patient", "id": "123", "name": [{"family": "Smith"}]}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient/123", {})
        finally:
            await client.close()

        assert result.success is True
        assert result.status_code == 200
        assert result.data["resourceType"] == "Patient"
        assert result.data["id"] == "123"

    @pytest.mark.asyncio
    async def test_get_with_params(self, httpx_mock):
        """Test GET request with query parameters."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient?family=Smith&gender=male",
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [{"resource": {"resourceType": "Patient", "id": "123"}}]
            }
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient", {"family": "Smith", "gender": "male"})
        finally:
            await client.close()

        assert result.success is True
        assert result.status_code == 200
        assert result.data["resourceType"] == "Bundle"
        assert len(result.data["entry"]) == 1

    @pytest.mark.asyncio
    async def test_get_404_error(self, httpx_mock):
        """Test GET request with 404 response."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient/nonexistent",
            status_code=404,
            json={"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "not-found"}]}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient/nonexistent", {})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 404
        assert "404" in result.error or "Not Found" in result.error

    @pytest.mark.asyncio
    async def test_get_500_error(self, httpx_mock):
        """Test GET request with 500 response."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient",
            status_code=500,
            json={"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "exception"}]}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient", {})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 500
        assert "500" in result.error or "Server Error" in result.error

    @pytest.mark.asyncio
    async def test_get_network_error(self, httpx_mock):
        """Test GET request with network error."""
        httpx_mock.add_exception(
            ConnectError("Connection refused")
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient", {})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 0
        assert "Connection" in result.error or "connect" in result.error.lower()


class TestFHIRClientPost:
    """Tests for POST requests."""

    @pytest.mark.asyncio
    async def test_post_success(self, httpx_mock):
        """Test successful POST request."""
        request_body = {
            "resourceType": "Patient",
            "name": [{"family": "Smith", "given": ["John"]}]
        }
        response_body = {
            "resourceType": "Patient",
            "id": "new-123",
            "name": [{"family": "Smith", "given": ["John"]}]
        }

        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient",
            method="POST",
            status_code=201,
            json=response_body
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.post("/fhir/Patient", request_body)
        finally:
            await client.close()

        assert result.success is True
        assert result.status_code == 201
        assert result.data["id"] == "new-123"

    @pytest.mark.asyncio
    async def test_post_validation_error(self, httpx_mock):
        """Test POST request with validation error (400)."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient",
            method="POST",
            status_code=400,
            json={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "invalid", "details": {"text": "Invalid resource"}}]
            }
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.post("/fhir/Patient", {"invalid": "data"})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 400
        assert "400" in result.error or "Bad Request" in result.error

    @pytest.mark.asyncio
    async def test_post_network_error(self, httpx_mock):
        """Test POST request with network error."""
        httpx_mock.add_exception(
            ConnectError("Connection refused"),
            method="POST"
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.post("/fhir/Patient", {"resourceType": "Patient"})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 0
        assert len(result.error) > 0


class TestFHIRClientExecute:
    """Tests for the execute() method that routes actions."""

    @pytest.mark.asyncio
    async def test_execute_get_action(self, httpx_mock):
        """Test execute routes GET actions correctly."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Observation?patient=123",
            json={"resourceType": "Bundle", "type": "searchset", "entry": []}
        )

        action = Action(
            type=ActionType.GET,
            endpoint="/fhir/Observation",
            params={"patient": "123"}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.execute(action)
        finally:
            await client.close()

        assert result.success is True
        assert result.data["resourceType"] == "Bundle"

    @pytest.mark.asyncio
    async def test_execute_post_action(self, httpx_mock):
        """Test execute routes POST actions correctly."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/MedicationRequest",
            method="POST",
            status_code=201,
            json={"resourceType": "MedicationRequest", "id": "med-456"}
        )

        action = Action(
            type=ActionType.POST,
            endpoint="/fhir/MedicationRequest",
            body={"resourceType": "MedicationRequest", "status": "active"}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.execute(action)
        finally:
            await client.close()

        assert result.success is True
        assert result.status_code == 201
        assert result.data["id"] == "med-456"

    @pytest.mark.asyncio
    async def test_execute_finish_action(self):
        """Test execute handles FINISH actions (no HTTP request)."""
        action = Action(
            type=ActionType.FINISH,
            answer="42"
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.execute(action)
        finally:
            await client.close()

        # FINISH doesn't make HTTP request, returns success with answer
        assert result.success is True
        assert result.data.get("answer") == "42"

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        """Test execute handles UNKNOWN actions."""
        action = Action(
            type=ActionType.UNKNOWN,
            raw_content="invalid content"
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.execute(action)
        finally:
            await client.close()

        assert result.success is False
        assert "unknown" in result.error.lower() or "unsupported" in result.error.lower()


class TestFHIRClientContextManager:
    """Tests for async context manager usage."""

    @pytest.mark.asyncio
    async def test_context_manager(self, httpx_mock):
        """Test using FHIRClient as async context manager."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient/123",
            json={"resourceType": "Patient", "id": "123"}
        )

        async with FHIRClient("http://localhost:8080") as client:
            result = await client.get("/fhir/Patient/123", {})

        assert result.success is True
        assert result.data["id"] == "123"


class TestFHIRClientEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_non_json_response(self, httpx_mock):
        """Test handling non-JSON response."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient/123",
            text="Not Found",
            status_code=404,
            headers={"Content-Type": "text/plain"}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient/123", {})
        finally:
            await client.close()

        assert result.success is False
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_params(self, httpx_mock):
        """Test GET request with empty params dict."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient",
            json={"resourceType": "Bundle", "type": "searchset", "entry": []}
        )

        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.get("/fhir/Patient", {})
        finally:
            await client.close()

        assert result.success is True

    @pytest.mark.asyncio
    async def test_base_url_trailing_slash(self, httpx_mock):
        """Test base URL with trailing slash is handled correctly."""
        httpx_mock.add_response(
            url="http://localhost:8080/fhir/Patient",
            json={"resourceType": "Bundle", "type": "searchset", "entry": []}
        )

        # Base URL with trailing slash
        client = FHIRClient("http://localhost:8080/")
        try:
            result = await client.get("/fhir/Patient", {})
        finally:
            await client.close()

        assert result.success is True
