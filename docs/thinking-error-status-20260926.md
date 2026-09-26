# Thinking status and actionable errors — 26 September 2026

User request: supplied Motion ShiningText and approximately one second of presentation for fast answers, plus accurate errors on public chat and staff forms. Scope remains existing chat/forms; no new tables, roles, uploads for public users or context-size warnings without evidence.

## Implementation
- components/ui/shining-text.tsx: typed Motion component adapted to span (status text, not a page heading), SCI colors, reduced-motion/static and forced-color fallback. Motion dependency; existing Tailwind4/TypeScript/@ alias retained, no provider required. Dedicated shining-text-demo.tsx keeps the prior FlowButton demo. No stock photos required.
- Thinking status starts immediately, before conversation creation. Successful fast responses wait only the remainder of 1000ms on the frontend; slower responses have no added second. Server response_time_ms still measures real work. Twelve-second message is based on elapsed time, not a fabricated percentage or claim that the model is thinking.
- Single in-flight guard; errors are shown immediately, draft restored; no automatic POST retries. History-refresh failure after a successful answer no longer pretends the send failed. Staff save/list-refresh similarly separated. Safe GET history check action lets users inspect whether an uncertain write completed.
- Shared request helper handles JSON/HTML proxy errors, network, timeout, 401/403/404/409/413/422/429/5xx, safe references, Retry-After. Existing upload flow uses the helper and clears stale errors. Upload/manage allow600s; other requests120s. A timeout does not claim the backend cancelled; warn to inspect stored results before resubmitting.
- Backend centralized safe JSON error codes, generated12hex request IDs, no raw exceptions/body/querystrings/credentials in error logging. Logs include request ID, route template, status and exception class/frame names/lines. Pydantic input is never echoed. Rate limit sends actual Retry-After. Retrieval-only degradation logged separately with request ID; existing truthful fallback answer retained.

## Validation
- Seven isolated backend tests (safeerrors + existing source links) passed with dummy SQLiteengine, no live DB writes. Source-link collection initially lackedDATABASE_URL; fixed isolated harness, not production settings.
- Node harness covers fast/slow minimum timing, success JSON, 10HTTPstatus categories, HTML proxy, invalidJSON, network and aborttimeout. First harness redeclared CommonJSexports; fixed harness then passed.
- Productionbuild/TS/diffcheck passed. Preview actual greeting showed shining preparing status with send disabled, then correct rule-based answer and history; no browser errors. No provider quota intentionally exhausted, no production fault injection, no authenticated CRUD submission; error cases simulated in isolated tests.
- Original new-chat icon-only/style change, staff-login transition, sidebar actions and official-source behavior preserved. No RAG provider/data/evidence change.

## Runtime/setup
Motion follows https://motion.dev/docs/react-animation . Components remain frontend/components/ui; styles frontend/app/style.css. Existing TypeScript/Tailwind setup needs no reinstall; npm ci installs pinned dependencies. Shadcn-style directory and alias already available; no shadcn CLI reset needed for this standalone component.
Release baseline06fa41e; immutable artifact + atomic current, restartSCIAPI/web only after idle, previousrelease rollback; no Nginx/env/DBchanges. PROJECT_STATE records final deployment evidence.
