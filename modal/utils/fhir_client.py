"""
Async FHIR Client for Sara

Provides async HTTP operations against a FHIR R4 server.
Used by the Sara agent orchestrator to execute actions parsed by the action parser.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

import httpx

from modal.utils.parser import Action, ActionType


@dataclass
class FHIRResult:
    """Result of a FHIR operation."""
    success: bool
    status_code: int
    data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""


class FHIRClient:
    """
    Async FHIR client for executing GET/POST requests against a FHIR server.

    Usage:
        async with FHIRClient("http://localhost:8080") as client:
            result = await client.get("/fhir/Patient/123", {})

        # Or manual lifecycle:
        client = FHIRClient("http://localhost:8080")
        try:
            result = await client.execute(action)
        finally:
            await client.close()
    """

    def __init__(self, base_url: str):
        """
        Initialize the FHIR client.

        Args:
            base_url: Base URL of the FHIR server (e.g., "http://localhost:8080")
        """
        # Remove trailing slash for consistent URL building
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"}
        )

    async def __aenter__(self) -> "FHIRClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def execute(self, action: Action) -> FHIRResult:
        """
        Execute an action against the FHIR server.

        Routes the action to the appropriate method based on action type.

        Args:
            action: Parsed action from Sara's output

        Returns:
            FHIRResult with success status, data, and any errors
        """
        if action.type == ActionType.GET:
            return await self.get(action.endpoint, action.params)
        elif action.type == ActionType.POST:
            return await self.post(action.endpoint, action.body)
        elif action.type == ActionType.FINISH:
            # FINISH action doesn't make HTTP request
            return FHIRResult(
                success=True,
                status_code=200,
                data={"answer": action.answer}
            )
        else:
            # UNKNOWN action type
            return FHIRResult(
                success=False,
                status_code=0,
                data={},
                error=f"Unsupported action type: {action.type}"
            )

    async def get(self, endpoint: str, params: Dict[str, str]) -> FHIRResult:
        """
        Execute a GET request against the FHIR server.

        Args:
            endpoint: FHIR endpoint path (e.g., "/fhir/Patient/123")
            params: Query parameters for the request

        Returns:
            FHIRResult with response data or error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self._client.get(url, params=params if params else None)
            return self._process_response(response)
        except httpx.ConnectError as e:
            return FHIRResult(
                success=False,
                status_code=0,
                data={},
                error=f"Connection error: {str(e)}"
            )
        except httpx.RequestError as e:
            return FHIRResult(
                success=False,
                status_code=0,
                data={},
                error=f"Request error: {str(e)}"
            )

    async def post(self, endpoint: str, body: Dict[str, Any]) -> FHIRResult:
        """
        Execute a POST request against the FHIR server.

        Args:
            endpoint: FHIR endpoint path (e.g., "/fhir/Patient")
            body: JSON body for the request

        Returns:
            FHIRResult with response data or error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self._client.post(url, json=body)
            return self._process_response(response)
        except httpx.ConnectError as e:
            return FHIRResult(
                success=False,
                status_code=0,
                data={},
                error=f"Connection error: {str(e)}"
            )
        except httpx.RequestError as e:
            return FHIRResult(
                success=False,
                status_code=0,
                data={},
                error=f"Request error: {str(e)}"
            )

    def _process_response(self, response: httpx.Response) -> FHIRResult:
        """
        Process an HTTP response into a FHIRResult.

        Args:
            response: httpx Response object

        Returns:
            FHIRResult with parsed data or error
        """
        status_code = response.status_code

        # Try to parse JSON response
        try:
            data = response.json()
        except Exception:
            data = {}

        # Check for HTTP errors (4xx, 5xx)
        if status_code >= 400:
            error_message = self._get_error_message(status_code, data)
            return FHIRResult(
                success=False,
                status_code=status_code,
                data=data,
                error=error_message
            )

        return FHIRResult(
            success=True,
            status_code=status_code,
            data=data
        )

    def _get_error_message(self, status_code: int, data: Dict[str, Any]) -> str:
        """
        Generate an error message from status code and response data.

        Args:
            status_code: HTTP status code
            data: Response body (may contain OperationOutcome)

        Returns:
            Human-readable error message
        """
        # Standard HTTP status messages
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable"
        }

        base_message = f"HTTP {status_code}: {status_messages.get(status_code, 'Error')}"

        # Try to extract details from OperationOutcome
        if data.get("resourceType") == "OperationOutcome":
            issues = data.get("issue", [])
            if issues:
                issue = issues[0]
                details = issue.get("details", {}).get("text", "")
                if details:
                    return f"{base_message} - {details}"

        return base_message
