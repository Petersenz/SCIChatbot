# Readable answers — 25 September 2026

Scope: presentation of grounded Thai answers only. No schema, role, menu, model, retrieval, thesis, or business-data change.
Use concise introductory paragraphs and single-level bullets; keep requested full lists and source qualifications. Do not add missing-data notices for topics the user did not ask. Direct questions without evidence still receive an honest unavailable answer. Stored conversation history remains unchanged.

Implementation: existing Gemini call gets system instructions; same rules are included in cache-key prompt. Plain-text list normalization preserves facts, citations, and missing-data notices; no post-generation semantic deletion. No second model call, extra worker, or dependency.

Verification on isolated VPS Git workspace:
- 14 unit/cache/retry tests passed; 3 DB-dependent tests excluded from this unit run.
- Initial test harness used wrong psycopg driver, then dummy DB produced 3 connection failures; not production failures, not counted as passed.
- Six read-only DB/live-generation scenarios: original question สนใจเกี่ยวกับคอมพิวเตอร์ แนะนำหน่อยครับ; explicit CS overview; complete eight careers; nonexistent tuition year2599; semester18credits; follow-up total121credits.
- Five Gemini answers + one expected no_evidence; no unasked absence footer in introductions. Exact-question generated response about600characters, citations retained. Does not guarantee every possible phrasing.
- Experiment with strict JSON/character limits rejected valid model output; removed before delivery. Final candidate uses existing text interface.
- No authenticated public CRUD retest in this change. Initial deployment's pending verification remains separate.

Deployment: preserve old0150250release, verify frontend unchanged, reuse its immutable build and dependencies, atomic current symlink switch, restart SCI API only when no established API connections. Health failure rolls symlink and SCI API back. No Nginx reload, existing-site mutation, database write/migration, or web-service restart.
Resource snapshot: 16GB RAM, about14GB available,36GB disk available. Remote QA one CPU/nice10; do not assume future bulk indexing is free of load.
Evidence stays private in /home/ubuntu/sci-chatbot-staging/20260925/readable-regression.json.

Reference: Google, Text generation, System instructions, accessed2026-09-25.
https://ai.google.dev/gemini-api/docs/text-generation#system-instructions
