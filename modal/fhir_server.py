# modal/fhir_server.py
# Deploy MedAgentBench HAPI FHIR server on Modal (CPU only)
# Provides /fhir/* endpoints with 100 pre-loaded patient profiles
#
# Setup:
#   pip install modal
#   modal setup
#
# Run:   modal run modal/fhir_server.py
# Deploy: modal deploy modal/fhir_server.py

import modal

from .config import (
    FHIR_CPU,
    FHIR_MEMORY,
    FHIR_CONCURRENT_INPUTS,
    MINUTES,
)

FHIR_IMAGE = "jyxsu6/medagentbench:latest"
FHIR_PORT = 8080
FHIR_TIMEOUT = 30 * MINUTES
FHIR_STARTUP_TIMEOUT = 5 * MINUTES

# --- Container image from MedAgentBench Docker ---
# The image has a built-in entrypoint that starts the HAPI FHIR server
# We preserve the entrypoint so Modal runs the default startup
image = modal.Image.from_registry(FHIR_IMAGE)

app = modal.App("fhir-server")


@app.function(
    image=image,
    cpu=FHIR_CPU,
    memory=FHIR_MEMORY,
    timeout=FHIR_TIMEOUT,
)
@modal.concurrent(max_inputs=FHIR_CONCURRENT_INPUTS)
@modal.web_server(port=FHIR_PORT, startup_timeout=FHIR_STARTUP_TIMEOUT)
def serve():
    """Start the HAPI FHIR server with pre-loaded MedAgentBench data.

    The MedAgentBench Docker image includes:
    - HAPI FHIR server (Java-based)
    - 100 pre-loaded synthetic patient profiles
    - Exposes /fhir/* endpoints on port 8080
    """
    import subprocess

    # Run the HAPI FHIR server using the image's default startup
    # The server runs as a Java WAR file on port 8080
    subprocess.Popen(
        ["java", "-jar", "/app/main.war"],
    )


# --- Local test entrypoint ---
@app.local_entrypoint()
def main():
    import json

    try:
        import aiohttp
    except ImportError:
        import subprocess as sp

        sp.run(["pip", "install", "aiohttp"], check=True)
        import aiohttp

    import asyncio

    async def test():
        url = serve.get_web_url()
        print(f"\nFHIR Server endpoint: {url}")
        print(f"FHIR base URL: {url}/fhir\n")

        async with aiohttp.ClientSession(base_url=url) as session:
            # Wait for server readiness by checking /fhir/metadata
            print("Waiting for FHIR server to be ready...")
            for attempt in range(60):
                try:
                    async with session.get(
                        "/fhir/metadata",
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers={"Accept": "application/fhir+json"},
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"Server is ready! FHIR version: {data.get('fhirVersion', 'unknown')}\n")
                            break
                except Exception as e:
                    if attempt % 10 == 0:
                        print(f"  Attempt {attempt + 1}/60: waiting...")
                await asyncio.sleep(5)
            else:
                print("FHIR server did not become ready in time.")
                return

            # Test a patient search
            print("Testing patient search...")
            async with session.get(
                "/fhir/Patient",
                params={"_count": "5"},
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Accept": "application/fhir+json"},
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    total = result.get("total", len(result.get("entry", [])))
                    print(f"Patient search successful!")
                    print(f"Total patients available: {total}")

                    # Show first few patient names
                    entries = result.get("entry", [])[:3]
                    if entries:
                        print("\nSample patients:")
                        for entry in entries:
                            patient = entry.get("resource", {})
                            names = patient.get("name", [])
                            if names:
                                name = names[0]
                                given = " ".join(name.get("given", []))
                                family = name.get("family", "")
                                patient_id = patient.get("id", "unknown")
                                print(f"  - {given} {family} (ID: {patient_id})")
                else:
                    print(f"Patient search failed with status: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text[:500]}")

    asyncio.run(test())
