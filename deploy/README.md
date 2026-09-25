# VPS deployment and recovery

## Deployment status — 2026-09-25

Live review URL: https://cstack.space/sci-chatbot/

Deployed application revision: `0150250ea988deb7473fad4d2f6eb7f60ec317b7` on `deploy/vps-setup`. A later documentation commit does not imply the live application has changed. Services `sci-chatbot-api` and `sci-chatbot-web` are enabled; PostgreSQL and both application ports listen on loopback only. Nginx was gracefully reloaded after syntax validation, with the prior config retained privately.

Restore verification: 50 document records, 798 chunks (768-dimensional embeddings), 29 uploaded files with matching checksums; counts of managed tables/relationships match the transfer manifest. Auth sessions, chat messages and conversations were excluded. This is a point-in-time migration, not ongoing synchronization with the development machine.

Checks passed: Linux production build and dependency consistency; three private live Gemini questions (major overview, semester credits, follow-up total); public browser health, logo, login page navigation, source PDF/image and 390px layout without overflow or page JavaScript errors. All three pre-existing sites returned 200 and their aggregate file hash stayed unchanged. Authenticated public CRUD/upload and a complete public chat journey still require a separate acceptance check; do not interpret these limited checks as full system certification.

First-launch requests briefly returned 404 immediately after the asynchronous Nginx reload. Subsequent direct-origin and public checks returned 200 without additional config changes. Keep readiness polling separate from the reload command's exit status.

Provisioning approval received 2026-09-25 for this host/application, including the PostgreSQL service account and the dedicated sci_chatbot database role. This is not standing permission for other accounts or later deployments.

Use `constraints.txt` with `backend/requirements.txt`; install `torch==2.9.1` from the official CPU wheel index first. Node runtime used for this deployment is 22.23.3. Embedding cache is pinned to revision `4328cf26390c98c5e3c738b4460a05b95f4911f5`, matching the local model. The private env sets EMBEDDING_MODEL to that snapshot directory. Service unit examples are specific to the inspected Ubuntu host, existing ubuntu account and runtime paths; review before reuse.

Target: Ubuntu 24.04, existing Nginx, public URL `/sci-chatbot/` on the existing HTTPS host.

## Required setup before activation

- Administrator prepares Node.js compatible with the locked Next.js version, Python venv support, PostgreSQL with pgvector, and a dedicated application database/connection. No existing database service was found in preflight. Do not create OS users, roles or grant privileges from these notes automatically.
- Keep source, releases, database dumps, uploads and environment files outside the shared Nginx document root. Suggested private project directory: `/home/ubuntu/apps/sci-chatbot/` using an already authorized runtime identity.
- Release layout: `releases/<commit>/`, `current` symlink, `shared/uploads`, private environment file and model cache. Never point the existing document root at application source.
- Frontend binds only `127.0.0.1:3110`; FastAPI only `127.0.0.1:8010`; PostgreSQL stays private. Do not open firewall ports for these services.
- Build with `NEXT_PUBLIC_BASE_PATH=/sci-chatbot` and `SCI_BACKEND_URL=http://127.0.0.1:8010`. Configure backend `SCI_ALLOWED_ORIGINS=https://cstack.space`. The prefix is a build-time setting.
- Build Node dependencies on Linux using `npm ci`; do not copy Windows node_modules or Python virtual environments. Cache the embedding model before startup. Limit build concurrency/resources while shared sites are active.

## Data migration

Transfer the private custom-format PostgreSQL dump and uploads archive over SSH, never GitHub. Dump preserves managed data, accounts/password hashes, documents/chunks/embeddings and relationships; excludes rows in auth_sessions, conversations and chats. Existing users must log in again. No plaintext account file or local .env is part of the package.

Restore into a NEW empty application database provided by the administrator, with `pg_restore --no-owner --no-acl --exit-on-error`. Do not use `--clean` against an existing database. Check row counts, sequences, relations, vector dimensions and every referenced upload against the manifest. Reuse existing vectors only with the same embedding model. Keep original localhost DB untouched. Data changes made locally after export require a fresh coordinated export before final activation.

## Verification and activation gate

1. Test the full prefix build locally: chat page, login, admin navigation, uploads, source links, images and responsive layout; API must remain under `/sci-chatbot/api/`.
2. Start the candidate privately only after the administrator has supplied runtime/database prerequisites. Confirm health and migrated data via SSH tunnel before public routing.
3. Preserve the existing Nginx config and all existing project hashes. Show the exact proposed include and rollback to Peter. `nginx-sci-chatbot.locations.conf` belongs INSIDE the existing HTTPS server block, not directly in conf.d.
4. Only after explicit approval: add the narrow include; run `nginx -t`; if it fails restore config without reload. If it passes, gracefully reload Nginx once. Do not restart it or change any existing project location.
5. Verify new URL, assets, cookies, uploads, chat/source/image flow, mobile and logs. Recheck all three existing URLs return 200 and their file hashes match the preflight manifest.

## Rollback / stop conditions

First deployment rollback: remove only the new include, restore exact prior config, validate then gracefully reload; stop only newly created SCI services. Keep the staged release and transfer package private for diagnosis. Later releases switch `current` back to the previous immutable release and restore its compatible database snapshot only under an approved data-loss/recovery plan. Do not delete old releases/backups in this task.

Stop before public activation on missing prerequisites, insufficient resources, bad config, checksum/data mismatch, failed login/upload/chat, unexpected permissions or any existing-project regression. Initial preflight does not prove these gates have passed.

Reference: https://nextjs.org/docs/app/api-reference/config/next-config-js/basePath
