# Open Exchange Submission Draft

## Name

Sara for IRIS

## Short Description

An InterSystems IRIS for Health FHIR AI agent that creates auditable Smart Patient Summaries through an Interoperability production and Embedded Python.

## Long Description

Sara for IRIS upgrades the Sara clinical workflow agent into an InterSystems-native FHIR agent. The app installs an IRIS for Health FHIR R4 endpoint, loads synthetic patient resources, exposes a REST task endpoint, routes summary requests through an Interoperability production, and executes deterministic clinical helper logic through an Embedded Python business process.

The main demo task is Smart Patient Summary Generator. Sara reads Patient, Condition, Observation, MedicationRequest, and ServiceRequest resources, calculates deterministic lab trends and follow-up rules, identifies magnesium/potassium replacement actions, flags missing A1C follow-up, and returns role-specific summaries for ED clinicians, care managers, and patients.

The frontend shows the evidence judges care about: FHIR resources retrieved from IRIS, production trace events, the Embedded Python component, and a FHIR SQL Builder-style query for lab trends.

Video walkthrough:

https://youtu.be/UAjI9O848wU?si=Gfm0aiaPbxqmB1Fy

## Features

- InterSystems IRIS for Health FHIR R4 server
- Interoperability production with traceable request flow
- Embedded Python summary process
- Smart Patient Summary Generator
- Deterministic clinical helper tools
- Modal-compatible API for online demos
- Next.js clinical artifact UI
- ZPM/IPM `module.xml`
- Docker compose file for judge setup
- Modal deployment path for reviewers who want to run IRIS, the API, the frontend, and Sara model inference in one cloud workspace

## Install

```bash
zpm "load /path/to/Sara"
```

Or for the local native install used during development:

```bash
scripts/setup_iris_native.sh
```

## Demo Request

```bash
curl -u "$IRIS_USERNAME:$IRIS_PASSWORD" \
  -X POST http://localhost:15273/sara/api/summary \
  -H 'Content-Type: application/json' \
  -d '{"patientId":"sara-demo-patient","role":"ed_clinician"}'
```

## Repository

https://github.com/Alfaxad/Sara

## Notes For Reviewers

The repository does not rely on a permanently hosted public demo because GPU and IRIS containers can incur cost. Reviewers can reproduce the full stack by following the Modal setup in `README.md`:

```bash
export MODAL_WORKSPACE='<your-modal-workspace-slug>'
modal deploy src/iris/modal_iris.py
modal deploy src/backend/sara_model.py
modal deploy src/backend/sara_iris_agent.py
modal deploy src/frontend/modal_app.py
```
