# Sara Security Pass - 2026-06-06

Scope: changed Sara for IRIS API, Modal model service, Modal frontend wrapper, frontend API/SSE client, and landing/chat UI changes.

## Threat Model

- Public browser users can load the hosted Modal frontend and trigger `/api/run`.
- Public API callers can reach the Sara for IRIS API directly.
- The model endpoint is deployed separately and protected by the existing `sara-api-key` Modal secret.
- The contest API currently serves bundled synthetic demo FHIR data when a live IRIS endpoint is unavailable from Modal.

## Findings And Fixes

- Fixed: unvalidated `Patient.id` input could be interpolated into FHIR resource paths. `SummaryRequest.patientId` now enforces the FHIR id character/length shape, and prompt-derived IDs are accepted only when they match the same pattern.
- Fixed: oversized API/model payloads could force excessive parsing or model work. `RunRequest`, `SummaryRequest`, and model chat messages now have bounded lengths and message count limits.
- Fixed: CORS origin regex is now anchored and includes only the known Vercel/Modal frontend patterns plus local development origins.
- Verified: the Modal model completion endpoint rejects unauthenticated requests with `401`; `/health` remains public for deployment health checks.

## Validation

- Backend focused tests: `47 passed`.
- Local invalid patient id: `POST /api/summary` with `../Observation` returns `422`.
- Local valid summary: returns `200`.
- Deployed invalid patient id: returns `422`.
- Deployed stream: returns `Sara.REST.TaskService`, `SaraPatientSummary`, and final ED clinician answer.
- Frontend production audit: `npm audit --omit=dev` reports `0 vulnerabilities`.
- Hosted frontend check: no current console errors, no runtime overlay, no connection error, trace/artifacts rendered.
- Model health: `https://nadhari--sara-model-serve.modal.run/health` returns `200`.

## Residual Risk

- Public `/api/run` is intentionally unauthenticated for the online demo and uses synthetic data. Add an API key, rate limit, or Modal usage guard before using non-demo data.
- The model inference endpoint is API-key protected; direct public completion testing requires the existing secret value, which was not read or exposed during this pass.
- This was a diff-scoped pass over the changed implementation, not an exhaustive repository-wide audit of all historical Sara code.
