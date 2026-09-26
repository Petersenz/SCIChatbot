# Provider-independent evidence and Groq trial

The user authorized fixing factual grounding and deploying Groq Free for review.
Baseline: 324e213. No UI/schema/business-data/embedding/role changes. The original thesis names Gemini; retain that adapter and record Groq as a user-requested trial, not an unchanged thesis technology claim. No original thesis edits.

Before: the same correctly retrieved table contained `รวม 18 14 8 32`; Groq interpreted the last column as credits. Prompt-only instructions failed twice. A broad introduction also invented careers/courses absent from its source.
Now: identify only explicit four-column course tables, verify unique rows, a single semester, and all four column sums before labelling each number. Unknown layouts are not guessed. Single-source semester-credit queries use verified table values; total-credit queries use current managed evidence. Broad introductions format existing descriptions without model-added facts. These rules apply to Gemini and Groq alike. Other questions still use RAG generation with normalized evidence. This is not a universal hallucination guarantee.

Groq adapter reuses httpx; production model openai/gpt-oss-120b, low reasoning. No automatic model rotation. Reject truncated output, preserve explicit errors/429, separate cache by evidence version/provider/model, never log secrets or raw provider responses. Existing bounded retry and rate limiter remain.

Verification: 25 unit tests passed, 3 DB-dependent tests excluded. Earlier harness runs used an unavailable psycopg driver and then an unused DB; these failures were not application regressions and were not counted as passes. Read-only actual DB validation: introduction, semester18, follow-up121, six courses with18 total, eight careers, news date/place/image_url, missing2599 and new-session clarification. No UI claim until post-deployment smoke. Tests throttle live provider calls; pacing is not model latency.

Rollout: immutable release, retain existing frontend build/dependencies, backup private env, atomically switch current, restart SCI API only after no active API connections. Do not reload Nginx or restart shared services. Rollback restores old symlink and env, then SCI API. Stop/rollback on health failure or original-case failure.

References: https://console.groq.com/docs/openai ; https://console.groq.com/docs/rate-limits ; https://console.groq.com/docs/models
