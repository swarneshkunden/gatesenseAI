# QA Deployment Readiness Report

Date: 2026-07-10
Project: Challenge 4 (React + Vite frontend + FastAPI backend)

## QA Scripts Executed
- Frontend build: `npm run build`
- Frontend lint: `npm run lint`
- Backend import smoke test: `python -c "import importlib; import main; print('import-ok')"`
- Backend endpoint smoke test: `curl http://127.0.0.1:8000/`
- Backend verification suite: `python verify_backend.py`

## Verified Results
- Frontend build: Failed
- Frontend lint: 1 warning
- Backend import: Passed
- Backend smoke test: Passed
- Backend verification suite: 83 passed, 6 failed, 1 warning

## Real Deployment Issues Found

### 1. Critical — Frontend build blocker
- The Vite frontend currently fails to build because `UserCheck` is referenced in [src/App.tsx](src/App.tsx) but is not imported or defined.
- Evidence: `npm run build` failed with `TS2304: Cannot find name 'UserCheck'`.
- Impact: The app cannot be deployed until this is fixed.

### 2. High — Frontend uses a hardcoded localhost backend URL
- The frontend is calling `http://127.0.0.1:8000` directly in [src/App.tsx](src/App.tsx).
- Impact: In production or on a remote deployment, the UI will point to the wrong backend and fail to connect unless the URL is changed.
- Recommended fix: Move this to an environment variable such as `VITE_API_BASE_URL`.

### 3. High — Backend binds to localhost by default
- The backend uses `127.0.0.1` as the default host in [server/config.py](server/config.py).
- Impact: In containerized or cloud deployments, the API may not be reachable from outside the container unless the host is explicitly configured to `0.0.0.0`.
- Recommended fix: Set host via environment variable and default to `0.0.0.0` in production.

### 4. High — CORS configuration is unsafe for production
- The backend enables `allow_origins=["*"]` while also allowing credentials in [server/main.py](server/main.py).
- Impact: This can cause browser-side CORS issues and is not a safe production policy.
- Recommended fix: Restrict allowed origins to known frontend domains.

### 5. Medium — Production startup mode is not appropriate
- The app starts Uvicorn with `reload=True` in [server/main.py](server/main.py).
- Impact: This is intended for development and is not suitable for production deployments.
- Recommended fix: Disable reload in production and run with a production-safe command.

### 6. Medium — AI features fall back to mock mode silently
- If `GEMINI_API_KEY` is absent, the backend runs in mock mode as shown in [server/gemini_service.py](server/gemini_service.py) and [server/main.py](server/main.py).
- Impact: Production behavior may look functional while silently skipping real AI responses.
- Recommended fix: Fail fast or clearly expose a warning/configuration error in production.

### 7. Medium — Rate limiting can block legitimate burst traffic
- The backend verification flow hit HTTP 429 for repeated CSV upload requests because the strict rate limiter was triggered in [server/routes/crowd.py](server/routes/crowd.py).
- Impact: Burst traffic, repeated file uploads, or real users under load may be blocked unexpectedly.
- Recommended fix: Tune limits for production traffic or apply them only to specific endpoints/clients.

## Recommended Priority Order
1. Fix the undefined `UserCheck` symbol so the frontend builds.
2. Replace hardcoded backend URLs with environment-based configuration.
3. Change backend host binding for production accessibility.
4. Tighten CORS to a specific allowlist.
5. Remove development-only startup flags from production deployment.

## Status
- Not deploy-ready yet
- Frontend blocker exists
- Backend is reachable locally, but production configuration still needs hardening
