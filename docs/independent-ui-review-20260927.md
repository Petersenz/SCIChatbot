# Independent UI/form review — 27 September 2026

Reviewer: independent UI sub-agent. Candidate inspected: remote `fix/context-scoped-retrieval` HEAD `b704bd9` plus pending frontend table filters/sort and double-scroll fix. This report reviews the candidate, not an assertion that Production has deployed it. No real accounts, credentials, uploaded files or Production records were changed.

## Method and actual coverage

Used ui-ux-pro-max accessibility/forms guidance. Browser used an isolated copy of the candidate frontend, fake GET data, and deliberately failing PATCH responses on private ports 3132/8132 (SSH-forwarded 13132). Own `.next` directory; no shared build/service mutation. Fixture role changes per page solely to render admin/staff screens; this does NOT test real authorization.

- Browser opened all 7 management pages and their add dialogs: users, majors, general, news, intents, curricula, careers. Read all rendered field labels, required flags and bounds; cancel without submission. User/account fields inspected only; no credentials entered or account operation submitted.
- All 4 report pages: dashboard, usage, satisfaction, unanswered; actual heading/column/filter correspondence checked.
- Profile page opened and inspected; no password changes or profile submissions.
- Mobile 375×812: all 12 admin pages fit root width, no unnamed buttons found by text/aria-label/title check. At 320×700 the careers filter panel also stayed within viewport. This is not a full WCAG certification or physical-device test.
- Career blank form submission blocked by native required validation and focused job title; no request made. Login blank submission focused username and required username/password flagged.
- Public entry, existing fixture history, three-dot menu, rename dialog, rating dialog and existing answer action controls rendered. Fake rename PATCH503 reproduced hidden error. Fake rating PATCH503 showed inline error, retained selected 4 stars, reenabled save. No actual LLM calls or Production conversations.
- Read shared component implementation for dialogs, uploads, forms, profile, reports, public chat and records. Did not execute real upload ingestion, all CRUD success/persistence, exports/file round-trip, screen-reader speech, OS reduced motion, real role authorization or every error permutation. Those require separate evidence.

## Findings and recommendations

| ID | Priority | Evidence | Finding and recommended fix |
|---|---|---|---|
| UI-01 | P2 correctness | Browser + code App.tsx Modal/Management | Dirty career draft closes immediately on X; no recovery. More importantly native dialog Escape closes even when close callback refuses because onCancel does not preventDefault. Root is preparing shared preventDefault plus guarded close/dirty confirmation. Recheck after patch. |
| UI-02 | P2 correctness | Code FieldInput/Management | Upload pending state lives in child; dialog close only checks save busy. Can close while upload still runs. Use existing data-uploading marker to block close and announce reason; root preparing fix. No upload sent in review. |
| UI-03 | P2 correctness | Browser fake503 + code public rename | Rename PATCH failure leaves modal open but error is in inert background chat; dialog text only contains title/field/Cancel/Save. Add inline modal error and pending lock. Separate committed-write success from history-refresh failure. Current Save can also be clicked repeatedly. |
| UI-04 | P2 consistency | Code management deletion / public delete | Deletion and following list refresh share one try/catch; successful delete followed by failed GET reads as a generic failure. Follow the existing management-save pattern: acknowledge committed mutation, warn only list refresh failed. Public delete also lacks pending guard. No actual delete attempted. |
| UI-05 | P2 accessibility | Code admin drawer | Mobile admin drawer lacks public drawer's Escape/focus-containment/return-focus behavior. Preserve existing structure but share the proven interaction. Needs keyboard browser verification after implementation. |
| UI-06 | P3 form guidance | Browser + backend/main.py276 | Intent prepared response remains optional in frontend even for rule_based, though API requires it. Add conditional required indicator/validation, disable or explain irrelevant field for RAG. No new table or business relation necessary. |
| UI-07 | P3 usability | Browser curriculum modal | With 31 career checkboxes fixture, dialog scrollHeight about2500px on375×812; save is far below fold. Suggest search-within-existing-choices and selected count, optionally sticky footer. Keep same curriculum-career relation, no new roles/menu/schema. |
| UI-08 | P3 guidance | Browser + code | Year and credits use generic '0 upwards' hint and INT32 maximum; that prevents technical overflow but not understandable year entry. Provide examples 'พ.ศ.2570' and business guidance first; do not impose arbitrary strict year range without agreed rule. Salary/fee labels should explicitly state monthly/per-term unit and estimate caveats. |
| UI-09 | P3 validation/help | Browser + code | Source URL has no placeholder/helper/maxlength unlike other URL fields. Image upload field lacks visible8MB limit; PDF has clear32MB/250pages helper. Align visible hints and backend constraints. Oversize file error does not clear input, so reselecting same oversized file may not re-trigger change. |
| UI-10 | P3 accessibility | Browser + code | Native required prompts appear in browser language (English in test). Server failures use one form-level alert without field links/focus summary. Retain native safety but add clear Thai inline field guidance and focusable summary for known server validation, avoiding intrusive validation on every keystroke. |

## Positive observations

Shared filter button has icon, expanded state, actual column labels and meaningful controls. Dropdowns derive from current loaded data; report table-only scope is stated. Headers use buttons and aria-sort. No new menu/table/role required. Rating is explicit-save and recovers from errors visibly. Required labels, email types, numeric minimum/steps, string limits, PDF/image selection and basic error announcements already exist. Public menu uses appropriate menu/menuitem roles. The current chapter3 page organization remains recognizable; recommendations focus on reliability and clear interaction rather than redesign.

## Limits and pending verification

No finding should be described as 'all web flows tested'. Real database write/ingestion/authentication and deployed release checks belong to root's release work. Parent will append final candidate fixes and exact post-fix results separately. Fixtures deliberately contain synthetic data; they establish UI behavior, not source correctness or curriculum-career appropriateness.

## Post-review patch check (same day)

Root prepared fixes for UI-01–04. Updated candidate code now prevents the native cancel default, checks management save/upload pending before close, adds dirty confirmation, puts rename/delete errors inside their dialogs, locks pending public mutations, and distinguishes successful write from failed list refresh. Code inspection supports those paths; these are not yet all independently browser-certified.

Attempting dirty-close confirmation in the isolated IAB tab triggered a CDP dispatch timeout. Subsequent getJsDialog/AX/close also timed out, and new-tab fallback was rejected because IAB visibility is unsupported in a sub-agent thread. This is an automation limitation at the native confirm interaction, not evidence that a user cannot use the confirmation. Decline/accept, Escape while pending and post-patch503 need parent verification or a later supported browser run. Initial pre-patch503 evidence above remains valid. No attempt was made to bypass browser controls.

Root subsequently chose an inline discard confirmation inside the same form dialog to avoid the native-confirm test limitation and provide explicit continue/discard controls. That final replacement will be verified by root; this reviewer did not browser-test the replacement. Own isolated fixture3132/8132 was stopped after validating process parentage and both Next processes' working directory. The stuck temporary IAB tab was reported to root; browser was not killed.
