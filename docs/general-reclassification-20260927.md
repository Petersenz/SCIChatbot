# General data ownership implementation — 27 September 2026

Target SCI Chatbot /sci-chatbot. User authorized reclassification preserving central information. Production activation/restart remains pending; no data moved yet.

Prepared data plan (tmp/general-reclassify/migration-plan.json, staging copy):
- Major12: preserve original description; append bounded staff/contact-address sections; use CS contact056-717122/comsci from existing general25; canonical source CSwebsite.
- Curriculum24: preserve year2570andexplicitintakeyearqualification/existingfile/relations; add sourceplanpage; no new curriculum or inferredyear mapping.
- General27: retain scholarshipconditions, rename central, explicitly no blanketeligibility.
- General29: retain commonstudentservices/links, rename centraluniversityservices.
- Retire general25,26,28 onlyafterdestinations/index succeed. Source snapshots retained in secure backup; historical citation URLs repointed in place without changing answer text/positions.
- Leave general30 unreadadmissionsimage and allunrelatedrows unchanged. Staffnames copied as stored; possible source name duplication not guessed corrected.

Code: genericboundedmajorsections forstaff/contact, planneronlyexplicitcommonlabels fallback forservices/scholarship/admission; scopedrecordspreferred, exclusivequeriescannotreceivecommonfallbackevenonfollowup. No schema/menu/newroles. Transactionmigrationchecksreviewedvalues,locksaffectedrecords,reindexesdestinations,removesobsoletechunks,rewritesaffectedhistorylinks; errors rollback. Backup/restore includes records/documents/vectors/affectedcitationmetadata. CLI defaults validation-only, requires explicitapply+newbackupfilemode0600.

Evidence:135backendtestsfirst; finalfullselected143pass2.14s; afterlockguard18affectedpass0.67s(overlapnotadditive). SQLitecopyofactualbusinessrows tests5retrievaldestinations,atomicmove,staleindexremoval,citationrepoint,restoreandfailure/concurrencyguards. Indexer in those migrationtests is a stub: not proof of real embedding/productionCRUD. InitialSQLitefixtureissues(bigintautoID/timezoneoffset) corrected fixtureonly, no weakerproductionguards. ProductionPGreadonlyplanvalidation4updates/3retirepass, committedfalse. NoLLM/webUIclaim, noProdDBwrite/restart/deploy.

Activation must pair reviewed backend with migration at idle; confirm health/resources/baseline/backup capacity first. Stop onrecorddiff,backup/index/errororjourneyfailure. Rollback through testedrestore undertransaction withcurrentdatachecks, thenpriorcode. Neverforce-overwrite subsequentstaffedits. Realindex andlive originalquestions/contact/commonservices/scholarships/plan/staff/crossmajors/sourcehistory require verification at rollout. Pendingcd2c479style/copycandidate remainsincludedintheworkingbranch but isnotimplicitlyauthorized forrelease.
