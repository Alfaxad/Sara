#!/usr/bin/env python3
"""Integration tests for Modal-deployed Sara and FHIR services.

This script verifies that both Modal services (sara-model and fhir-server)
are deployed and communicating correctly.

Usage:
    python -m modal.test_services
    # or
    python modal/test_services.py
"""

import sys
import httpx
import modal

# Test configuration
TIMEOUT = 60.0  # seconds for HTTP requests
SARA_APP_NAME = "sara-model"
SARA_FUNCTION_NAME = "serve"
FHIR_APP_NAME = "fhir-server"
FHIR_FUNCTION_NAME = "serve"


def get_service_url(app_name: str, function_name: str) -> str | None:
    """Get the deployed URL for a Modal service."""
    try:
        fn = modal.Function.from_name(app_name, function_name)
        url = fn.web_url
        if url:
            return url.rstrip("/")
        return None
    except Exception as e:
        print(f"  Error getting URL for {app_name}/{function_name}: {e}")
        return None


def test_fhir_health(fhir_url: str) -> bool:
    """Test FHIR server health by checking /fhir/metadata endpoint."""
    print("\n[TEST 1] FHIR Server Health Check")
    print(f"  Endpoint: {fhir_url}/fhir/metadata")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                f"{fhir_url}/fhir/metadata",
                headers={"Accept": "application/fhir+json"},
            )

        if response.status_code == 200:
            data = response.json()
            fhir_version = data.get("fhirVersion", "unknown")
            print(f"  Status: OK (HTTP {response.status_code})")
            print(f"  FHIR Version: {fhir_version}")
            return True
        else:
            print(f"  Status: FAILED (HTTP {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"  Status: FAILED")
        print(f"  Error: {e}")
        return False


def test_sara_health(sara_url: str) -> bool:
    """Test Sara model health by checking /health endpoint."""
    print("\n[TEST 2] Sara Model Health Check")
    print(f"  Endpoint: {sara_url}/health")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{sara_url}/health")

        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            print(f"  Status: OK (HTTP {response.status_code})")
            print(f"  Health Status: {status}")
            return True
        else:
            print(f"  Status: FAILED (HTTP {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"  Status: FAILED")
        print(f"  Error: {e}")
        return False


def test_fhir_patient_fetch(fhir_url: str) -> tuple[bool, str | None]:
    """Test fetching a patient from FHIR server."""
    print("\n[TEST 3] FHIR Patient Fetch")
    print(f"  Endpoint: {fhir_url}/fhir/Patient?_count=1")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                f"{fhir_url}/fhir/Patient",
                params={"_count": "1"},
                headers={"Accept": "application/fhir+json"},
            )

        if response.status_code == 200:
            data = response.json()
            entries = data.get("entry", [])

            if entries:
                patient = entries[0].get("resource", {})
                patient_id = patient.get("id", "unknown")
                names = patient.get("name", [])

                if names:
                    name = names[0]
                    given = " ".join(name.get("given", []))
                    family = name.get("family", "")
                    full_name = f"{given} {family}".strip()
                else:
                    full_name = "Unknown"

                print(f"  Status: OK (HTTP {response.status_code})")
                print(f"  Patient ID: {patient_id}")
                print(f"  Patient Name: {full_name}")
                return True, patient_id
            else:
                print(f"  Status: FAILED (no patients found)")
                return False, None
        else:
            print(f"  Status: FAILED (HTTP {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False, None

    except Exception as e:
        print(f"  Status: FAILED")
        print(f"  Error: {e}")
        return False, None


def test_sara_fhir_query(sara_url: str, patient_id: str) -> bool:
    """Test Sara model with a FHIR-related question."""
    print("\n[TEST 4] Sara Model FHIR Query")
    print(f"  Endpoint: {sara_url}/v1/chat/completions")
    print(f"  Question: What query would you use to find conditions for patient {patient_id}?")

    try:
        payload = {
            "model": "Alfaxad/Sara-1.5-4B-it",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"You are an expert in using FHIR functions to assist medical professionals.\n\n"
                        f"Question: What FHIR query would you use to find all conditions for patient {patient_id}?"
                    ),
                }
            ],
            "max_tokens": 256,
            "temperature": 0.0,
        }

        with httpx.Client(timeout=TIMEOUT * 2) as client:  # Longer timeout for inference
            response = client.post(
                f"{sara_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            print(f"  Status: OK (HTTP {response.status_code})")
            print(f"  Response: {content[:300]}...")
            print(f"  Tokens: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}")
            return True
        else:
            print(f"  Status: FAILED (HTTP {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"  Status: FAILED")
        print(f"  Error: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Sara Modal Services Integration Tests")
    print("=" * 60)

    # Get service URLs
    print("\nDiscovering deployed services...")

    fhir_url = get_service_url(FHIR_APP_NAME, FHIR_FUNCTION_NAME)
    sara_url = get_service_url(SARA_APP_NAME, SARA_FUNCTION_NAME)

    if not fhir_url:
        print(f"\nERROR: Could not get URL for {FHIR_APP_NAME}. Is it deployed?")
        print("  Deploy with: modal deploy modal/fhir_server.py")
        sys.exit(1)

    if not sara_url:
        print(f"\nERROR: Could not get URL for {SARA_APP_NAME}. Is it deployed?")
        print("  Deploy with: modal deploy modal/sara_model.py")
        sys.exit(1)

    print(f"  FHIR Server: {fhir_url}")
    print(f"  Sara Model:  {sara_url}")

    # Run tests
    results = {}

    # Test 1: FHIR health
    results["fhir_health"] = test_fhir_health(fhir_url)

    # Test 2: Sara health
    results["sara_health"] = test_sara_health(sara_url)

    # Test 3: FHIR patient fetch
    patient_success, patient_id = test_fhir_patient_fetch(fhir_url)
    results["fhir_patient"] = patient_success

    # Test 4: Sara FHIR query (only if we have a patient ID)
    if patient_id:
        results["sara_query"] = test_sara_fhir_query(sara_url, patient_id)
    else:
        print("\n[TEST 4] Sara Model FHIR Query")
        print("  Status: SKIPPED (no patient ID from test 3)")
        results["sara_query"] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll services are working correctly!")
        sys.exit(0)
    else:
        print("\nSome tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
