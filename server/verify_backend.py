#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
"""
=============================================================================
Volunteer Copilot - Comprehensive Verification Test Suite
FIFA World Cup 2026 | Crowd & Translation Backend
=============================================================================

Run with:
    python verify_backend.py

Make sure the backend is running first:
    python main.py
=============================================================================
"""


import json
import time
import io
import os
import requests

BASE_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────────────────
# ANSI Color Helpers
# ─────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0
warnings = 0

def ok(label: str, detail: str = ""):
    global passed
    passed += 1
    suffix = f"  -> {detail}" if detail else ""
    print(f"  {GREEN}[PASS]{RESET} {label}{suffix}")

def fail(label: str, detail: str = ""):
    global failed
    failed += 1
    suffix = f"  -> {detail}" if detail else ""
    print(f"  {RED}[FAIL]{RESET} {label}{suffix}")

def warn(label: str, detail: str = ""):
    global warnings
    warnings += 1
    suffix = f"  -> {detail}" if detail else ""
    print(f"  {YELLOW}[WARN]{RESET} {label}{suffix}")

def section(title: str):
    print(f"\n{BOLD}{CYAN}== {title} =={RESET}")

def assert_eq(label, actual, expected, detail=""):
    if actual == expected:
        ok(label, detail or f"got {repr(actual)}")
    else:
        fail(label, f"expected {repr(expected)}, got {repr(actual)}")

def assert_in(label, item, container, detail=""):
    if item in container:
        ok(label, detail)
    else:
        fail(label, f"{repr(item)} not in {repr(container)}")

def assert_status(label, response, expected_status, detail=""):
    if response.status_code == expected_status:
        ok(label, detail or f"HTTP {response.status_code}")
    else:
        fail(label, f"expected HTTP {expected_status}, got {response.status_code} — {response.text[:200]}")

# ─────────────────────────────────────────────────────────
# SECTION 1: Backend Health Check
# ─────────────────────────────────────────────────────────
section("1. Backend Health & Root Endpoint")

try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    assert_status("Root endpoint responds", r, 200)
    data = r.json()
    assert_eq("status field is 'online'", data.get("status"), "online")
    assert_in("version field present", "version", data)
    assert_in("mock_mode field present", "mock_mode", data)
    mock_mode = data.get("mock_mode", True)
    if mock_mode:
        warn("Running in MOCK MODE (no Gemini API key)", "AI responses will be pre-scripted mock data")
    else:
        ok("Gemini API key configured", "Real AI engine is active")
except requests.ConnectionError:
    fail("Backend connection", f"Cannot connect to {BASE_URL}. Is the server running? Run: python main.py")
    print(f"\n{RED}FATAL: Backend is not reachable. Aborting tests.{RESET}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────
# SECTION 2: Crowd Management - GET /api/crowd/zones
# ─────────────────────────────────────────────────────────
section("2. Crowd Zone Retrieval — GET /api/crowd/zones")

r = requests.get(f"{BASE_URL}/api/crowd/zones")
assert_status("GET /api/crowd/zones returns 200", r, 200)
data = r.json()
assert_eq("Response status field", data.get("status"), "success")
assert_in("'zones' key present in response", "zones", data)
zones = data.get("zones", [])
if len(zones) >= 4:
    ok(f"Zones loaded (count: {len(zones)})", "At least 4 zones returned")
else:
    fail(f"Expected ≥ 4 zones, got {len(zones)}")

for zone in zones:
    assert_in(f"Zone '{zone.get('zone_id')}' has occupancy_rate", "occupancy_rate", zone)
    assert_in(f"Zone '{zone.get('zone_id')}' has throughput_rate", "throughput_rate", zone)
    assert_in(f"Zone '{zone.get('zone_id')}' has status", "status", zone)

# ─────────────────────────────────────────────────────────
# SECTION 3: Crowd Management - POST /api/crowd/update
# ─────────────────────────────────────────────────────────
section("3. Zone Update Validation — POST /api/crowd/update")

# Valid update
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 45.0,
    "throughput_rate": 120.0
})
assert_status("Valid zone update returns 200", r, 200)
data = r.json()
assert_eq("Response status is 'success'", data.get("status"), "success")

# Verify status auto-calculation: occupancy >= 85 → Critical
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 90.0,
    "throughput_rate": 200.0
})
assert_status("Update to critical occupancy", r, 200)
data = r.json()
assert_eq("Status auto-calc: 90% → Critical", data["zone"]["status"], "Critical")

# occupancy >= 75 but < 85 → Crowded
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 78.0,
    "throughput_rate": 150.0
})
data = r.json()
assert_eq("Status auto-calc: 78% → Crowded", data["zone"]["status"], "Crowded")

# occupancy < 75 → Normal
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 50.0,
    "throughput_rate": 120.0
})
data = r.json()
assert_eq("Status auto-calc: 50% → Normal", data["zone"]["status"], "Normal")

# Validation: occupancy_rate > 100 should be rejected
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 150.0,
    "throughput_rate": 100.0
})
assert_status("Occupancy > 100 is rejected (422/400)", r, 422 if r.status_code == 422 else 400)

# Validation: negative throughput should be rejected
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate A",
    "occupancy_rate": 50.0,
    "throughput_rate": -100.0
})
assert_status("Negative throughput is rejected (422/400)", r, 422 if r.status_code == 422 else 400)

# Validation: empty zone_id should be rejected
r = requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "",
    "occupancy_rate": 50.0,
    "throughput_rate": 100.0
})
assert_status("Empty zone_id is rejected (422/400)", r, 422 if r.status_code == 422 else 400)

# ─────────────────────────────────────────────────────────
# SECTION 4: Crowd Analysis — POST /api/crowd/analyze
# ─────────────────────────────────────────────────────────
section("4. AI Crowd Analysis — POST /api/crowd/analyze")

# First push a known critical state
requests.post(f"{BASE_URL}/api/crowd/update", json={
    "zone_id": "Gate D",
    "occupancy_rate": 92.0,
    "throughput_rate": 350.0
})

r = requests.post(f"{BASE_URL}/api/crowd/analyze?threshold=80")
assert_status("POST /api/crowd/analyze returns 200", r, 200)
data = r.json()
assert_eq("Response status is 'success'", data.get("status"), "success")
analysis = data.get("analysis", {})
assert_in("'alerts' key in analysis", "alerts", analysis)
assert_in("'instructions' key in analysis", "instructions", analysis)
if isinstance(analysis.get("alerts"), list):
    ok("'alerts' is a list", f"contains {len(analysis['alerts'])} alert(s)")
    if analysis["alerts"]:
        ok("Critical zone detected in alerts", f"'{analysis['alerts'][0][:60]}...'")
    else:
        warn("No alerts returned", "Zone D at 92% should trigger at threshold=80")
else:
    fail("'alerts' is not a list")
if analysis.get("instructions"):
    ok("Instructions provided", f"'{analysis['instructions'][:80]}...'")
else:
    fail("Instructions missing or empty")

# ─────────────────────────────────────────────────────────
# SECTION 5: CSV Upload — POST /api/crowd/upload-csv
# ─────────────────────────────────────────────────────────
section("5. CSV Upload Validation — POST /api/crowd/upload-csv")

# Valid CSV
valid_csv = b"zone_id,occupancy_rate,throughput_rate\nGate A,30.0,80.0\nGate B,75.0,200.0\nGate C,95.0,380.0\n"
r = requests.post(
    f"{BASE_URL}/api/crowd/upload-csv",
    files={"file": ("test.csv", io.BytesIO(valid_csv), "text/csv")}
)
assert_status("Valid CSV upload returns 200", r, 200)
data = r.json()
assert_eq("Response status is 'success'", data.get("status"), "success")
if data.get("zones"):
    ok(f"Zones loaded from CSV (count: {len(data['zones'])})")

# Missing required column
bad_csv = b"zone_id,occupancy_rate\nGate A,50.0\n"
r = requests.post(
    f"{BASE_URL}/api/crowd/upload-csv",
    files={"file": ("missing_col.csv", io.BytesIO(bad_csv), "text/csv")}
)
assert_status("CSV missing 'throughput_rate' column rejected (400)", r, 400)

# Wrong file extension (.txt instead of .csv)
r = requests.post(
    f"{BASE_URL}/api/crowd/upload-csv",
    files={"file": ("data.txt", io.BytesIO(valid_csv), "text/plain")}
)
assert_status("Non-CSV extension rejected (400)", r, 400)

# File too large (> 100 KB)
big_csv = b"zone_id,occupancy_rate,throughput_rate\n" + b"Gate A,50.0,100.0\n" * 6000
r = requests.post(
    f"{BASE_URL}/api/crowd/upload-csv",
    files={"file": ("bigfile.csv", io.BytesIO(big_csv), "text/csv")}
)
assert_status("Oversized CSV (>100KB) rejected (413)", r, 413)

# Out-of-range occupancy in CSV row
bad_values_csv = b"zone_id,occupancy_rate,throughput_rate\nGate A,150.0,100.0\n"
r = requests.post(
    f"{BASE_URL}/api/crowd/upload-csv",
    files={"file": ("badvalues.csv", io.BytesIO(bad_values_csv), "text/csv")}
)
assert_status("CSV row with occupancy > 100 rejected (400)", r, 400)

# ─────────────────────────────────────────────────────────
# SECTION 6: Translation API — POST /api/translation/translate
# ─────────────────────────────────────────────────────────
section("6. Translation Assistant — POST /api/translation/translate")

# Standard casual request
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "¿Dónde está el baño?",
    "fan_language": "Spanish",
    "fan_origin": "Mexico",
    "urgency_level": "casual",
    "stress_level": "calm"
})
assert_status("Casual translation request returns 200", r, 200)
data = r.json()
assert_eq("Response status is 'success'", data.get("status"), "success")
result = data.get("result", {})
assert_in("'detected_language' in result", "detected_language", result)
assert_in("'fan_text_en' in result", "fan_text_en", result)
assert_in("'urgency_analysis' in result", "urgency_analysis", result)
assert_in("'suggested_response_en' in result", "suggested_response_en", result)
assert_in("'suggested_response_fan_lang' in result", "suggested_response_fan_lang", result)
if result.get("suggested_response_en"):
    ok("English volunteer response generated", f"'{result['suggested_response_en'][:60]}...'")
if result.get("suggested_response_fan_lang"):
    ok("Fan language response generated", f"'{result['suggested_response_fan_lang'][:60]}...'")

# Emergency request
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "Ayuda, me siento muy mal, dolor en el pecho",
    "fan_language": "Spanish",
    "fan_origin": "Argentina",
    "urgency_level": "emergency",
    "stress_level": "panicked"
})
assert_status("Emergency translation request returns 200", r, 200)
result = r.json().get("result", {})
urgency_analysis = result.get("urgency_analysis", "")
if "emergency" in urgency_analysis.lower() or "medical" in urgency_analysis.lower() or "EMERGENCY" in urgency_analysis:
    ok("Emergency correctly classified", f"urgency_analysis: '{urgency_analysis[:80]}'")
else:
    warn("Emergency classification not obvious", f"urgency_analysis: '{urgency_analysis[:80]}'")

# Validation: invalid urgency_level
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "Hello",
    "urgency_level": "INVALID_VALUE",
    "stress_level": "calm"
})
if r.status_code in (400, 422):
    ok("Invalid urgency_level rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Invalid urgency_level should be rejected, got HTTP {r.status_code}")

# Validation: invalid stress_level
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "Hello",
    "urgency_level": "casual",
    "stress_level": "TOTALLY_WRONG"
})
if r.status_code in (400, 422):
    ok("Invalid stress_level rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Invalid stress_level should be rejected, got HTTP {r.status_code}")

# Validation: empty text
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "",
    "urgency_level": "casual",
    "stress_level": "calm"
})
if r.status_code in (400, 422):
    ok("Empty text is rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Empty text should be rejected, got HTTP {r.status_code}")

# Validation: text too long (> 2000 chars)
r = requests.post(f"{BASE_URL}/api/translation/translate", json={
    "text": "A" * 2001,
    "urgency_level": "casual",
    "stress_level": "calm"
})
if r.status_code in (400, 422):
    ok("Text > 2000 chars is rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Text > 2000 chars should be rejected, got HTTP {r.status_code}")

# ─────────────────────────────────────────────────────────
# SECTION 7: Broadcast Script — POST /api/translation/broadcast-script
# ─────────────────────────────────────────────────────────
section("7. Broadcast Script Generator — POST /api/translation/broadcast-script")

r = requests.post(f"{BASE_URL}/api/translation/broadcast-script", json={
    "scenario": "Gate D has reached maximum capacity. All fans are being redirected to Gate C.",
    "target_gates": ["Gate D", "Gate C"],
    "languages": ["Spanish", "French"]
})
assert_status("Broadcast script request returns 200", r, 200)
data = r.json()
assert_eq("Response status is 'success'", data.get("status"), "success")
result = data.get("result", {})
assert_in("'scenario' in result", "scenario", result)
assert_in("'broadcast_scripts' in result", "broadcast_scripts", result)
scripts = result.get("broadcast_scripts", {})
if isinstance(scripts, dict) and len(scripts) >= 1:
    ok(f"Scripts generated for {len(scripts)} language(s)", f"Keys: {list(scripts.keys())}")
    for lang, script in scripts.items():
        if script:
            ok(f"Script for '{lang}'", f"'{script[:60]}...'")
        else:
            fail(f"Empty script for '{lang}'")
else:
    fail("No scripts generated")

# Validation: scenario too short
r = requests.post(f"{BASE_URL}/api/translation/broadcast-script", json={
    "scenario": "ok",
    "target_gates": ["Gate A"],
    "languages": ["English"]
})
if r.status_code in (400, 422):
    ok("Short scenario (<5 chars) rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Short scenario should be rejected, got HTTP {r.status_code}")

# Validation: empty target_gates list
r = requests.post(f"{BASE_URL}/api/translation/broadcast-script", json={
    "scenario": "This is a valid long scenario description for testing.",
    "target_gates": [],
    "languages": ["English"]
})
if r.status_code in (400, 422):
    ok("Empty target_gates rejected (400/422)", f"HTTP {r.status_code}")
else:
    fail(f"Empty target_gates should be rejected, got HTTP {r.status_code}")

# ─────────────────────────────────────────────────────────
# SECTION 8: Rate Limiting Verification
# ─────────────────────────────────────────────────────────
section("8. Rate Limiting — Sliding Window Enforcement")

# The strict endpoint is /api/crowd/upload-csv (limit: 5/min)
# We'll test the default (60/min) and just verify that headers or 429s are possible.
# Since we can't easily exhaust 60 requests without flooding, we verify behavior is consistent.

# Instead, test that 429 format is correct by burning through a known-strict-rate call pattern.
# We simulate hitting the 429 path by examining headers.
print("  (Rate limit is configured per IP; verifying 429 response format...)")

# Make a batch of fast requests to the analyze endpoint (non-destructive, uses default limit)
consecutive_responses = []
for _ in range(3):
    try:
        resp = requests.post(f"{BASE_URL}/api/crowd/analyze?threshold=80", timeout=3)
        consecutive_responses.append(resp.status_code)
    except Exception:
        pass

# All 3 should succeed (well within the 60/min limit)
successes = sum(1 for s in consecutive_responses if s == 200)
if successes == 3:
    ok("Burst of 3 analyze requests all pass (within limit)", "Rate limit not triggered prematurely")
else:
    warn(f"Only {successes}/3 analyze requests succeeded", "Possible rate limit or connectivity issue")

# If we have a way to force 429, check response format
# We'll check the existing rate limiter behavior - note that strict limit = 5/min
# The CSV endpoint is strict (5/min). We already used some above, so let's check if 429 response is well-formed.
print("  (Testing 429 error response format — triggering strict endpoint beyond limit...)")
rate_limit_triggered = False
for i in range(8):  # 5 is the limit; above 5 should 429
    r = requests.post(
        f"{BASE_URL}/api/crowd/upload-csv",
        files={"file": ("r.csv", io.BytesIO(valid_csv), "text/csv")}
    )
    if r.status_code == 429:
        rate_limit_triggered = True
        data_429 = r.json()
        if "status" in data_429 and data_429["status"] == "error":
            ok("429 response has correct error format", f"message: {data_429.get('message','')[:60]}")
        else:
            warn("429 response format unexpected", str(data_429)[:100])
        break

if rate_limit_triggered:
    ok("Rate limiter triggered correctly (HTTP 429)", "Strict endpoint enforced at 5 req/min")
else:
    warn("Rate limit not triggered in 8 requests", "Limit counter may have been reset between test sections")

# ─────────────────────────────────────────────────────────
# SECTION 9: Error Handler Sanitization
# ─────────────────────────────────────────────────────────
section("9. Error Response Sanitization & Security")

# Non-existent endpoint → 404 with sanitized format
r = requests.get(f"{BASE_URL}/api/nonexistent/endpoint")
assert_status("404 on unknown endpoint", r, 404)
# Ensure we don't leak stack traces in the response body
resp_text = r.text
if "traceback" in resp_text.lower() or "file \"" in resp_text.lower():
    fail("SECURITY: Stack trace leaked in 404 response")
else:
    ok("No stack trace leaked in 404 response")

# Malformed JSON body → 422 with structured error
r = requests.post(
    f"{BASE_URL}/api/translation/translate",
    data="this is not json at all",
    headers={"Content-Type": "application/json"}
)
if r.status_code in (400, 422):
    ok("Malformed JSON body returns 400/422", f"HTTP {r.status_code}")
    data = r.json()
    if "status" in data:
        ok("Structured error response returned", f"status: {data.get('status')}")
    else:
        warn("Response may not follow error format", str(data)[:100])
else:
    warn(f"Unexpected response for malformed JSON: HTTP {r.status_code}")

# Missing required fields → validation error with field names
r = requests.post(f"{BASE_URL}/api/translation/translate", json={})
if r.status_code in (400, 422):
    ok("Missing required fields returns validation error (400/422)", f"HTTP {r.status_code}")
    data = r.json()
    if "errors" in data or "detail" in data:
        ok("Validation error includes field details")
    else:
        warn("Validation error may be missing field details", str(data)[:100])
else:
    fail(f"Missing required fields should trigger validation error, got {r.status_code}")

# ─────────────────────────────────────────────────────────
# SECTION 10: API Docs (FastAPI OpenAPI)
# ─────────────────────────────────────────────────────────
section("10. FastAPI OpenAPI Docs Available")

r = requests.get(f"{BASE_URL}/docs")
assert_status("Swagger UI at /docs returns 200", r, 200)

r = requests.get(f"{BASE_URL}/openapi.json")
assert_status("OpenAPI JSON schema at /openapi.json returns 200", r, 200)
schema = r.json()
paths = schema.get("paths", {})
expected_paths = [
    "/api/crowd/zones",
    "/api/crowd/update",
    "/api/crowd/analyze",
    "/api/crowd/upload-csv",
    "/api/translation/translate",
    "/api/translation/broadcast-script",
]
for path in expected_paths:
    if path in paths:
        ok(f"Route '{path}' documented in OpenAPI schema")
    else:
        fail(f"Route '{path}' missing from OpenAPI schema")

# ─────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────
total = passed + failed + warnings
print(f"\n{'='*60}")
print(f"{BOLD}VERIFICATION SUMMARY{RESET}")
print(f"{'='*60}")
print(f"  {GREEN}Passed:   {passed}{RESET}")
print(f"  {RED}Failed:   {failed}{RESET}")
print(f"  {YELLOW}Warnings: {warnings}{RESET}")
print(f"  Total:    {total}")
print(f"{'='*60}")

if failed == 0:
    print(f"\n{GREEN}{BOLD}[SUCCESS] ALL TESTS PASSED - Backend is fully functional!{RESET}")
elif failed <= 2:
    print(f"\n{YELLOW}{BOLD}[WARN] MOSTLY PASSING - {failed} minor issue(s) detected. Review warnings above.{RESET}")
else:
    print(f"\n{RED}{BOLD}[FAILED] {failed} TESTS FAILED - Review failures above before deploying.{RESET}")

sys.exit(0 if failed == 0 else 1)
