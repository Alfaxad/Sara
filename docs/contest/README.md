# Sara for IRIS Contest Edition

Sara for IRIS upgrades the original Modal + HAPI FHIR demo into an InterSystems IRIS for Health FHIR agent submission.

## Implemented Contest Surface

- InterSystems IRIS for Health FHIR R4 endpoint: `/fhir/r4`
- ZPM/IPM package metadata: `module.xml`
- IRIS namespace installer: `Sara.Setup`
- Interoperability production: `Sara.Interop.Production`
- REST dispatch endpoint: `/sara/api`
- Embedded Python business process: `Sara.Interop.AgentProcess`
- Smart Patient Summary Generator
- Deterministic helper tools for age, latest labs, averages, magnesium/potassium dosing, and A1C follow-up detection
- Frontend artifacts for IRIS FHIR reads, Interoperability traces, SQL evidence, and Smart Patient Summary
- Modal-compatible contest API: `src/backend/sara_iris_agent.py`
- YouTube walkthrough: https://youtu.be/UAjI9O848wU?si=Gfm0aiaPbxqmB1Fy

## Native IRIS Setup

The local machine already has IRIS Health Community installed at:

```bash
/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris
```

Start the local instance:

```bash
export IRISSYS=/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry
/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry/iris start PELAGIA quietly
```

Load the package:

```bash
export IRIS_USERNAME=_SYSTEM
export IRIS_PASSWORD='your-local-iris-password'
scripts/setup_iris_native.sh
```

On macOS native installs, Embedded Python may require the Homebrew Python version that the IRIS kit was linked against. This local kit expects Python 3.11:

```bash
brew install python@3.11
```

The script imports `src/iris`, stages Python/demo assets into the IRIS manager directory, installs the FHIR server, loads the demo bundle, creates `/sara/api`, configures the agent process with the secured local FHIR endpoint, and enables `Sara.Interop.Production`.

Stop the instance when done:

```bash
export IRISSYS=/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry
/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry/iris stop PELAGIA quietly
```

## Endpoints

FHIR:

```text
GET http://localhost:15273/fhir/r4/Patient/sara-demo-patient
```

Sara REST:

```text
GET  http://localhost:15273/sara/api/health
POST http://localhost:15273/sara/api/summary
```

Example request:

```bash
curl -u "$IRIS_USERNAME:$IRIS_PASSWORD" \
  -H 'Content-Type: application/json' \
  -d '{"patientId":"sara-demo-patient","role":"ed_clinician","now":"2026-06-05T12:00:00+00:00"}' \
  http://localhost:15273/sara/api/summary
```

For the Modal/local FastAPI API to read a secured IRIS FHIR endpoint directly, set:

```bash
export IRIS_FHIR_URL=http://localhost:15273/fhir/r4
export IRIS_FHIR_USERNAME="$IRIS_USERNAME"
export IRIS_FHIR_PASSWORD="$IRIS_PASSWORD"
```

## Frontend Setup

Run the contest API locally:

```bash
uvicorn src.backend.sara_iris_agent:local_app --reload --port 8000
```

Run the frontend:

```bash
cd src/frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open:

```text
http://localhost:3000
```

Select `IRIS Patient Summary`.

## Modal Deployment

Modal is used to run the IRIS server, public API, frontend, and model inference layer in one reproducible workspace. A permanent public Modal demo is intentionally not required because GPU and IRIS containers can incur cost.

Set your Modal workspace slug:

```bash
export MODAL_WORKSPACE='<your-modal-workspace-slug>'
```

Create the required Modal secrets:

```bash
modal secret create sara-api-key SARA_API_KEY='<choose-a-long-random-key>'
modal secret create huggingface-nadhari HF_TOKEN='<your-huggingface-token>'
modal secret create sara-iris-password \
  IRIS_PASSWORD='<choose-a-long-random-password>' \
  IRIS_FHIR_USERNAME='_SYSTEM' \
  IRIS_FHIR_PASSWORD='<same-password-as-IRIS_PASSWORD>'
```

Deploy the full stack:

```bash
MODAL_WORKSPACE="$MODAL_WORKSPACE" modal deploy src/iris/modal_iris.py
modal deploy src/backend/sara_model.py
MODAL_WORKSPACE="$MODAL_WORKSPACE" modal deploy src/backend/sara_iris_agent.py
MODAL_WORKSPACE="$MODAL_WORKSPACE" modal deploy src/frontend/modal_app.py
```

Expected endpoints:

- Frontend: `https://<workspace>--sara-frontend-serve.modal.run`
- Sara for IRIS API: `https://<workspace>--sara-for-iris-api.modal.run`
- IRIS FHIR: `https://<workspace>--sara-iris-health-serve.modal.run/fhir/r4`
- Sara model service: `https://<workspace>--sara-model-serve.modal.run`

For a public deployment, set `SARA_IRIS_API_KEY` and pass it as either `X-API-Key` or `Authorization: Bearer ...`.

For Docker, export an IRIS password before startup:

```bash
export IRIS_PASSWORD='replace-with-a-local-dev-password'
docker compose -f docker-compose.iris.yml up
```

## Judge Walkthrough

1. Open the app and select `IRIS Patient Summary`.
2. Watch Sara stream the IRIS trace event.
3. Inspect the `IRIS FHIR Read Set` artifact.
4. Inspect `Smart Patient Summary`.
5. In the summary artifact, show:
   - deterministic medication/lab actions
   - `Sara.Interop.Production`
   - Embedded Python process name
   - FHIR SQL Builder query
6. In IRIS Management Portal, open Interoperability > View > Messages and show the request through `Sara.REST.TaskBusinessService` and `Sara.Interop.AgentProcess`.
7. Open the FHIR endpoint and show the loaded patient resources.

## Bonus Checklist

- Suggested task: Smart Patient Summary Generator
- InterSystems FHIR Server: implemented
- Embedded Python: implemented through `Sara.Interop.AgentProcess`
- LLM: original Sara agent/model remains available, and the contest API is compatible with the Sara frontend stream contract
- Docker: `docker-compose.iris.yml` provided for judges
- ZPM/IPM: `module.xml` provided
- Vector Search: artifact-ready hook documented as optional-ready in `irisEvidence.vectorSearch`
- Online demo: reproducible through Modal deployment instructions
- Article: left to the submitter
- YouTube video: https://youtu.be/UAjI9O848wU?si=Gfm0aiaPbxqmB1Fy
