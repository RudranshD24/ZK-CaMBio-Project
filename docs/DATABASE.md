# DATABASE.md
PostgreSQL in Docker (SQLite allowed for unit tests). ORM: SQLAlchemy 2.x + Alembic.

## Tables
**users**: `id UUID PK`, `username UNIQUE`, `created_at`, `active BOOL`

**templates**: `id UUID PK`, `user_id FK`, `key_version INT`, `template BYTEA` (m bits packed), `m INT`, `algo_version TEXT`, `created_at`, `revoked_at NULL`

**user_keys**: `id`, `user_id FK`, `key_version INT`, `key_material BYTEA` (encrypted at rest with an app-level master key from env), `created_at`, `revoked_at NULL`
Keeping keys in a separate table from templates makes the threat-model cases explicit: (A) templates leak alone, (B) templates + keys leak.

**audit_log**: `id`, `user_id`, `event` (enroll/verify/identify/revoke), `result`, `score`, `ts`  (no biometric data)

## Rules
- Only one active template per (user, key_version); revocation sets `revoked_at` and creates a new key_version.
- Never store: images, embeddings, fused vectors.
- Indexes: `templates(user_id, revoked_at)`.
