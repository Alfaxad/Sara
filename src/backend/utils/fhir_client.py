"""
Async FHIR Client for Sara

Provides async HTTP operations against a FHIR R4 server.
Used by the Sara agent orchestrator to execute actions parsed by the action parser.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict

import httpx

from src.backend.utils.parser import Action, ActionType


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

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1.5

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 120.0,
        max_retries: int | None = None,
        retry_delay_seconds: float | None = None,
        auth: tuple[str, str] | httpx.Auth | None = None,
    ):
        """
        Initialize the FHIR client.

        Args:
            base_url: Base URL of the FHIR server (e.g., "http://localhost:8080")
        """
        # Remove trailing slash for consistent URL building
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries if max_retries is not None else self.MAX_RETRIES
        self.retry_delay_seconds = (
            retry_delay_seconds if retry_delay_seconds is not None else self.RETRY_DELAY_SECONDS
        )
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=timeout_seconds),
            headers={
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            follow_redirects=True,
            auth=auth,
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
        url = self._build_url(endpoint)
        request_params = dict(params) if params else {}
        request_params.setdefault("_format", "json")
        return await self._request_with_retry("GET", url, params=request_params)

    async def post(self, endpoint: str, body: Dict[str, Any]) -> FHIRResult:
        """
        Execute a POST request against the FHIR server.

        Args:
            endpoint: FHIR endpoint path (e.g., "/fhir/Patient")
            body: JSON body for the request

        Returns:
            FHIRResult with response data or error
        """
        url = self._build_url(endpoint)
        return await self._request_with_retry("POST", url, json=body)

    async def put(self, endpoint: str, body: Dict[str, Any]) -> FHIRResult:
        """
        Execute a PUT request against the FHIR server.

        Args:
            endpoint: FHIR endpoint path (e.g., "/fhir/Patient/123")
            body: JSON body for the resource

        Returns:
            FHIRResult with response data or error
        """
        url = self._build_url(endpoint)
        return await self._request_with_retry("PUT", url, json=body)

    def _build_url(self, endpoint: str) -> str:
        """Join a FHIR base URL and action endpoint without duplicating /fhir."""
        normalized = endpoint
        if self.base_url.endswith("/fhir") and normalized.startswith("/fhir"):
            normalized = normalized[5:]
        if self.base_url.endswith("/fhir/r4") and normalized.startswith("/fhir/r4"):
            normalized = normalized[8:]
        return f"{self.base_url}{normalized}"

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> FHIRResult:
        """Execute an HTTP request with bounded retries for transient failures."""
        last_error = "Unknown request error"
        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    response = await self._client.get(url, **kwargs)
                elif method == "POST":
                    response = await self._client.post(url, **kwargs)
                elif method == "PUT":
                    response = await self._client.put(url, **kwargs)
                else:
                    return FHIRResult(
                        success=False,
                        status_code=0,
                        data={},
                        error=f"Unsupported HTTP method: {method}",
                    )
                return self._process_response(response)
            except httpx.TimeoutException as exc:
                last_error = f"Timeout: {repr(exc)}"
            except httpx.ConnectError as exc:
                last_error = f"Connection error: {repr(exc)}"
            except httpx.RequestError as exc:
                last_error = f"Request error: {type(exc).__name__}: {repr(exc)}"
            except Exception as exc:
                last_error = f"Unexpected error: {type(exc).__name__}: {str(exc)}"

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))

        return FHIRResult(success=False, status_code=0, data={}, error=last_error)

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
