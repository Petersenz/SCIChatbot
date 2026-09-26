# Independent code review — SCI Chatbot — 27 September 2026

Reviewed by an independent sub-agent at Peter's explicit request. Review target: remote workspace branch `fix/context-scoped-retrieval`, HEAD `b704bd9`, combined candidate against live baseline `48e75d5666cc36da0fd586c8d027c74f5986a722`. Current frontend changes were also inspected at the shared table-query helper level. This is a bounded code/retrieval review, not full UI or security certification.

No application edits, production writes, service changes, or external model calls were made by this reviewer. Read-only DB probes used `SET TRANSACTION READ ONLY` and default read-only connection options. Pure planner probes used SQLite configuration without a database connection. Existing project state/test matrix read before review. Current production relation data has 21 careers linked to curriculum24; old missing-link status was not assumed.

## Findings sent to primary agent before release

### CR-01 — P1 — Faculty-wide requests can silently keep the previous major

Location before fix: `backend/conversation_plan.py:189,239–242`; `backend/query_understanding.py:83–97`.

Reproduce: previous question `วิทย์คอมมีทุนไหม`, next exact question `คณะมีทุนอะไรบ้าง`.

Observed planner `major_names=()` correctly marks faculty-wide scope, but query text is `วิทยาการคอมพิวเตอร์ คณะมีทุนอะไรบ้าง`. Legacy resolver receives the old plan and re-injects the major because its broad-scope vocabulary differs from the new planner. Actual read-only retrieval returns `/records/general/27` (CS scholarship). This can incorrectly substitute one major's information for faculty-wide information.

Minimal fix: broad scope must clear incompatible inherited slots *before* calling the resolver; maintain one broad-scope detector/invariant. Add regression asserting both slot state and actual source identity, not just `major_names`.

### CR-02 — P2 — Broad career follow-up remains stuck on the previous job

Location before fix: `backend/conversation_plan.py:210–219`.

Reproduce: `วิทย์คอมจบไปทำเว็บได้ไหม` → `วิทย์คอมมีอาชีพอะไรบ้าง`.

Observed query appends `นักพัฒนาเว็บและโมบายด์แอปพลิเคชัน` and retains that entity. Actual read-only retrieval returns only `/records/careers/3`, although current curriculum24 links 21 careers. Planner's broad-career reset vocabulary omits `อาชีพอะไรบ้าง`, already recognized by the older resolver.

Minimal fix: use a shared broad-career detector in both layers, clear inherited career entities/focus, preserve major/year scope. Regress both new broad question and specific salary follow-up so the latter still retains its job.

### CR-03 — P1 — An empty scoped general selection is treated as unscoped semantic search

Location before fix: `backend/conversation_plan.py:231–238`; `backend/structured_evidence.py:57–104`; `backend/rag.py:136–141,184–192`.

Fresh questions `ทุนของคณะมีอะไรบ้าง` and `ของคณะมีอาจารย์กี่คน` have route scholarship/staff and zero eligible faculty-level general entities. Actual read-only `retrieve_managed` returns `None`, meaning delegate to semantic search rather than no evidence. The vector query can include major-specific general records because there are no entity IDs and no major slot. Fixing CR-01 alone does not remove this follow-on path.

Minimal fix: represent a completed scoped catalog lookup separately from an unspecified lookup; an empty completed result must stay empty. A narrow general-only route guard is sufficient for scholarship/staff/services/history/mission. Contact and admissions include other public tables, so preserve their legitimate major/news handling explicitly. Test a catalog containing CS records but no faculty records, and assert no fallback to those CS records.

### CR-04 — P2 recommendation — Compound questions silently lose one requested data domain

Location: `backend/conversation_plan.py:detect_route`, first matching TOPICS route, then `requested_fields`; retrieval follows only that route.

Actual read-only probe: `วิทย์คอม ค่าเทอมเท่าไหร่ แล้วจบไปเงินเดือนเท่าไหร่`.
Planner records both `salary_start` and `tuition_fee`, but chooses tuition and retrieves only `/records/curricula/12` and `/records/curricula/24`. No career salary evidence is passed downstream. No model was called; this review claims missing evidence coverage, not an observed generated response. This limitation also exists in the older single-topic approach.

Recommendation: either retrieve the two independent supported sections or ask which topic to answer first when requested fields require incompatible source categories. Do not allow a generic answer to imply that salary data is absent from the system. Treat as bounded follow-up improvement if not part of the release fix.

## Review checks without a new finding

- Chat API calls `own_conversation` before session history loading. SQL continues to filter `Chat.session_id == id`; history projects questions and source URLs, not cross-user answer bodies.
- Public planner catalog is an explicit five-table allowlist. Users/auth/report tables are not eligible public evidence.
- Static intent exact matching requires an entire utterance; disabled and tied intents do not get selected arbitrarily. Semantic fallback is constrained to short unknown-route inputs and caches configured examples rather than user utterances.
- Career membership uses `CurriculumCareer` SQL filtering before role matching. Empty scoped career retrieval does not broaden to unrelated global career vectors.
- Shared table-query filtering runs before pagination; range checks are inclusive, dropdowns derive from loaded authorized rows, missing values sort last. This is source review only; UI agent owns interaction/accessibility verification.

## Limits and handoff

The primary agent was notified of CR-01 through CR-03 as release-relevant and is responsible for implementation and regression verification. This report records the pre-fix evidence and is not a statement that later candidate revisions remain faulty. Update disposition after reviewing the exact final patch. No claim of exhaustive security/performance review or all possible Thai phrasing coverage is made.

## Independent verification of primary agent fixes

After root introduced `general_scope_resolved`, broad scope clearing before resolver, and shared `broad_career_question`, seven read-only retrieval checks passed:

- CS scholarship → faculty scholarship: zero sources, no CS substitution.
- Fresh faculty scholarship: zero sources.
- Faculty staff count: zero sources, no CS substitution.
- CS web role → all CS careers: all 21 linked career sources.
- CS web role → salary: only career3 retained.
- Faculty contact: general1 retained.
- CS scholarship: general27 retained.

### CR-05 — P2 — Guard fix initially blocked admission news

New guard applied to admissions even though its allowed tables include news. Exact queries `มีข่าวรับสมัครอะไรบ้าง` and `ข่าวรับสมัคร` returned no sources. Temporarily clearing the flag on the in-memory plan (no file/DB change) restored `/records/news/39` through the existing admissions news filter. Sent to root for correction and a regression. `ข่าวรับสมัครล่าสุด` was not suitable evidence because existing stored news has no qualifying published-date result; both paths correctly returned empty for that latest-date query. No unsupported publication date was inferred.

### CR-06 — P2 — Contact fallback emits title-only evidence when all contact fields are absent

The new empty-general guard initially returned a major source even if tel/email/website/Facebook were all empty, because `major_name_th` was included unconditionally. Read-only probe `ขอเบอร์ติดต่อเคมี` returned only `major_name_th: เคมี`. Same condition exists on majors2,5,6,7,9,10. Existing lower contact branch correctly returned empty if no actual contact fields. This wastes model work and can invite a citation to a source that does not answer the contact question. Minimal correction: require at least one actual contact value before emitting the source. Sent to root; no changes to other majors' data requested or performed.

## Final disposition — independently verified after root corrections

All six findings above have a corresponding bounded fix in the current workspace. A final nine-case read-only check passed after the latest changes (no LLM/API generation, no chat rows written):

| Check | Observed result |
|---|---|
| CS scholarship → faculty-wide scholarship | No CS source substitution; zero eligible sources |
| CS web career → all CS careers | 21 linked career sources |
| CS web career → salary | Only career3 |
| `มีข่าวรับสมัครอะไรบ้าง` | news39 restored |
| `ข่าวรับสมัคร` | news39 restored |
| Contact for major with all contact fields absent | Zero sources |
| Faculty contact | general1 preserved |
| CS scholarships | general27 preserved |
| Tuition and career salary in one question | Explicit clarification: choose curriculum or career first |

CR-04 is addressed conservatively through clarification, not simultaneous multi-domain answering. This is an intentional current limitation; it should not be reported as a multi-topic answer capability. Counts overlap earlier checks and are not summed into a larger independent test total.

No remaining release-blocking finding was identified in the bounded reviewed paths after these checks. This does not certify all Thai utterances, every production UI interaction, or current factual accuracy of each underlying record. Production deployment and post-deployment verification belong to the primary agent; this reviewer tested the workspace candidate read-only against current data.
