# Answer copy and readable structure — 27 September 2026

Target: SCI Chatbot /sci-chatbot. Current live b79bff4; this candidate includes pending natural-tone f1151d6. No deployment or business-data writes in this task.

## Root causes and changes
- CopyAnswer explicitly appended numbered references and URLs. Shared copyAnswerText now removes resolved citation tokens and does not append a bibliography; preserves ordered numbers, dates, salaries, unknown bracketed numbers and explicit URLs.
- AnswerText previously rendered each line as generic divs. Shared AnswerContent now renders semantic headings, paragraphs and ordered/unordered lists. Legacy vision/mission labels are normalized too. Identical list citations grouped once; mixed-source lists retain per-item provenance.
- Shared provider prompt requests concise sections and appropriate lists across topics while preserving caveats and source facts.
- Formal general-information statements use exact managed heading contents when complete and unambiguous. Missing/duplicate sections and explanation/summary requests defer to generation. No fixed answer text or record ID in implementation.
- Actual database probe caught query expansion adding unwanted sections to philosophy-only questions. Formal-section selection now uses the original question; retrieval still uses contextual query. Added regression.

## Evidence
- Actual read-only PostgreSQL: exact Peter question `วิสัยทัศน์และพันธกิจ ของคณะคืออะไร` returns general/3, two headings and five original mission items; combined philosophy/vision/mission returns three headings; philosophy-only returns one. All three grounded, no LLM required. Latest-news probe still returns news/75 without storage-date narration.
- Backend final regression: 125 passed in 1.89s (XML in staging answer-layout-tests.xml). Earlier failure was existing lambda test double not accepting the new keyword argument; updated mock signature and reran complete selection.
- Node assertion harness: numeric preservation, clean copy, headings/list rendering, repeated/mixed sources and HTML escaping pass. Existing additional-source regression passes.
- Next production build and TypeScript pass. git diff --check passes. Source newline normalization prevents CRLF-only churn.
- Private browser fixture renders the actual backend answer with two headings/five list items; copy button success status; console errors zero. Virtual clipboard returned empty and paste reported no data, so actual OS paste is NOT certified. Screenshot tmp/answer-layout/preview.png.
- No live user chat write, no Production mutation, no new dependencies/schema/menu/roles. Not a certification of all topics/models or mobile browsers.

## Release
Prepare immutable combined candidate with rebuilt frontend. Approval required for activation under AGENTS.md Production baseline. On approved release, verify service health/capacity and current baseline first; switch only SCI current symlink and restart SCI API/web using existing scoped runbook, then exact user journey/copy checks plus news and legacy-site boundaries. Roll back current to b79bff4 if health/journey fails. No DB migration/cache clearing/Nginx/shared-service changes. Brief SCI restart impact must be checked and accepted at release time.
