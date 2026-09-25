# Chat interface — 25 September 2026
User approved replacing inline raw citations with links, a three-dot conversation menu, staff login at sidebar bottom, and moving the brand into the sidebar without a duplicate top header.
UI-only change; no schema, backend, permissions, RAG, stored history or thesis edits.
Keep yellow as accent; plain answer background, single-level readable paragraphs/bullets, source titles in accessible links mapped from existing citation indices. Unknown references remain text rather than fabricating links; no raw HTML rendering. Source details and existing image links remain.
Conversation menu preserves rename/rating/delete confirmation; Escape/outside click and arrow navigation. Mobile sidebar traps keyboard focus and Escape restores the trigger.
Remote one-CPU production build passed. First build failed because Turbopack disallows external node_modules symlink; copied existing Linux dependencies into isolated workspace and rebuilt successfully, no runtime/dependency version change.
Private preview at loopback3111 via SSH tunnel. Welcome/sidebar visually inspected; 320/375/390/414/768 widths no root horizontal overflow; mobile open/close/Escape passed.
Activation uses new immutable release and current symlink, restart SCI web only, preserve previous release. Nginx, backend and database unchanged. Public chat/source/menu smoke checks follow activation; initial authenticated CRUD backlog is separate.
