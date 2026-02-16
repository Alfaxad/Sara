# src/backend/fhir_server.py
# Deploy MedAgentBench HAPI FHIR server on Modal
# Uses multi-stage Dockerfile to get data from jyxsu6/medagentbench
#
# Setup:
#   pip install modal
#   modal setup
#
# Run:   modal run src/backend/fhir_server.py
# Deploy: modal deploy src/backend/fhir_server.py

import modal
from pathlib import Path

# --- Config ---
MINUTES = 60
FHIR_PORT = 8080
FHIR_TIMEOUT = 60 * MINUTES

app = modal.App("fhir-server")

# Build image from multi-stage Dockerfile
dockerfile_path = Path(__file__).parent / "Dockerfile.fhir"
image = modal.Image.from_dockerfile(dockerfile_path)


@app.function(
    image=image,
    cpu=2.0,
    memory=4096,
    timeout=FHIR_TIMEOUT,
)
@modal.concurrent(max_inputs=100)
@modal.web_server(port=FHIR_PORT, startup_timeout=5 * MINUTES)
def serve():
    """Start the HAPI FHIR server with pre-loaded MedAgentBench data.

    The MedAgentBench Docker image (jyxsu6/medagentbench:latest) includes:
    - HAPI FHIR server (Java-based)
    - 100 pre-loaded synthetic patient profiles (in H2 database)
    - Exposes /fhir/* endpoints on port 8080
    """
    import subprocess
    import os

    os.chdir("/app")

    # Start the HAPI FHIR server using the same command as the Docker image
    # This uses the configs/application.yaml which points to /data/test_db
    subprocess.Popen(
        [
            "java",
            "-Xmx2g",
            "--class-path", "/app/main.war",
            "-Dloader.path=main.war!/WEB-INF/classes/,main.war!/WEB-INF/,/app/extra-classes",
            "-Dspring.config.location=/configs/application.yaml",
            "org.springframework.boot.loader.PropertiesLauncher",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


# --- Local test entrypoint ---
@app.local_entrypoint()
def main():
    import asyncio

    try:
        import aiohttp
    except ImportError:
        import subprocess as sp
        sp.run(["pip", "install", "aiohttp"], check=True)
        import aiohttp

    async def test():
        url = serve.get_web_url()
        print(f"\nFHIR Server endpoint: {url}")
        print(f"FHIR base URL: {url}/fhir\n")

        async with aiohttp.ClientSession() as session:
            # Wait for server readiness
            print("Waiting for FHIR server to be ready...")
            for attempt in range(60):
                try:
                    async with session.get(
                        f"{url}/fhir/metadata",
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers={"Accept": "application/fhir+json"},
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"Server is ready! FHIR version: {data.get('fhirVersion', 'unknown')}\n")
                            break
                except Exception:
                    if attempt % 10 == 0:
                        print(f"  Attempt {attempt + 1}/60: waiting...")
                await asyncio.sleep(5)
            else:
                print("FHIR server did not become ready in time.")
                return

            # Test a patient search
            print("Testing patient search...")
            async with session.get(
                f"{url}/fhir/Patient",
                params={"_count": "5"},
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Accept": "application/fhir+json"},
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    total = result.get("total", len(result.get("entry", [])))
                    print(f"Patient search successful!")
                    print(f"Total patients available: {total}")

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
