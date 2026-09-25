# VPS staging plan (not yet deployed)

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
