# News recency correction — 27 September 2026

Target: SCI Chatbot, https://cstack.space/sci-chatbot/. Live baseline20600067a1c7af03e033018481716f617fe82cac; candidate branchfix/news-managed-recency based on documentation-followupe23dcbe. No production mutation in this task.

## Reproduction and root cause

Exact user question: `ข่าวล่าสุดคือข่าวอะไร` (new conversation, no injected major/year).
Production news75 is the newly added Google Student Ambassador Thailand item, created2026-09-27T07:32:09Z. Document exists, title agrees with managed row,2chunks exist. No missing-upload/index evidence. Previous retrieval selectednews10/EdPEx because latest selector admitted only explicit publication-date labels inside news content. New row has no such publication label. Adding a correct news record through existing form was therefore insufficient for generic latest query.

Prior test asserted news10 for a generic latest request; this encoded a product semantics mismatch. Corrected definition: generic latest means latest added record in this managed system; explicitly published/posted/latest-on-website questions use only evidenced publication dates with existing coverage qualification. Never call created_at an event or publication date. No inference/change to source publication dates, no new table/field/menu or thesis edits.

## Candidate

- news_recency shared helper selects managed created_at after existing major/year/event constraints; stableid tie-break; missingtimestamps do not infer dates fromid; naiveUTC/awaretimestamps normalized.
- Headline latest questions read title/date directly and return existing citation/image path, without generation/embedding/cache dependence. Event-detail questions continue grounded generation.
- Explicit publication recency behavior preserved; updated old tests to explicitly request that behavior and added separate tests for generic managed recency.
- News latest is a fresh lookup, preserving applicable major scope but clearing stale event/title/year from previous-event reference. Followup `ข่าวนี้มีใครบ้าง` retains selectedsource identity.
- Insert/edit/delete test in isolatedSQLite proves fresh reads and no stale generation-cache result for latest headline. No reindex or business-data rewrite required.

## Results

-143passed1deselected1dependencydeprecationwarning,8.13seconds. Selected suites newsrecency/conversationplan/newscompletion/newssources/contextrouting/ragcoverage/conversationscope/coreAPIisolated/answertone/groundedevidence. One existingProductionwrite test excluded, isolatedAPI tests retained. No summed overlapping40test preliminaryrun.
-8actualDBreadonly retrieval cases: genericlatest75, newestfaculty75, publishedlatest10, CSlatest62, oldSmartStart→latest75, latest→participants75, namedGoogle75, SmartStartplace39. Exactuserquestion fullanswer returnsmodegrounded/newtitle75, no paidLLMcall.
- Newrecord document exists/titlematches/2chunks. No write to news/documents/embeddings/chats; no account/credential change. No actualnewLLMdetailaccuracy/UI/productionrelease certification in this task.
- gitdiffcheck passes; backend-only change, frontend/build/dependencies untouched.

## Release candidate and gates

Prepare immutable archive fromexactcandidate plus unchangedfrontend/.next fromcurrentlive release. Beforeactivation verifycurrent still2060006, idleSCIconnections, health71documents/839chunks expected only if freshhealthconfirms (do not hardcode counts), freeRAM/disk andnginx-t. Atomiccurrent switch and restartonlySCIAPI; webartifactidentical andwebprocess mayremainoldcompatiblefrontend. BriefAPIunavailability duringrestart boundedbyreadinesspoll. Stop/rollback onnotready,DBcountdrift,newerrororoldsitesregression. Rollbackcurrent→2060006 and restartonlySCIAPI,verifyhealth. NoNginxreload/DBmigration. Activationrequirescurrenttask-specificapproval perPeterProductionSafetyBaseline; previousrequest'sreleaseapprovaldoesnotcarryforward.

Remaininglimits: created_at meansaddednotupdated; importingoldnewsnow makesitlatestaddedwithhonestlabel. Publicationorderonlyincludesrecordswithexplicitdateevidence. No claimallThaiutterancesunderstood. Sourcefactaccuracyunchanged.
