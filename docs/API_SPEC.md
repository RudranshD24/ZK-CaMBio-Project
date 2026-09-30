# API Specification (FastAPI, JSON + Multipart)

Authentication: Static Bearer token via `Authorization: Bearer <API_TOKEN>` header (configured via `API_TOKEN` environment variable).
*Note: In production deployments, this would be replaced with an OAuth2 / OIDC JWT provider.*

---

## 1. Key Modes (ADR D-016)

Every enrolled user is registered with one of two key modes:
1. **`user_secret` (Default & Recommended)**:
   - The user supplies a private PIN or passphrase (`user_secret`) at enrollment and during verification.
   - The server derives the chaos parameters dynamically in memory:
     $$\text{key} = \text{HMAC-SHA256}(\text{app\_salt}, \text{user\_secret} \parallel \text{key\_version})$$
   - **Zero key material is persisted on the server**.
   - **Identification (`/identify`) is disabled** for this user to prevent brute-forcing unkeyed databases.
   - If an adversary breaches the database, templates cannot be decrypted or transformed without the user's secret.

2. **`server_key` (Opt-in for 1:N Identification)**:
   - The server derives a random 256-bit key encrypted with `AES-256-GCM` using the server-side master key (`SERVER_MASTER_KEY`).
   - Stored in the isolated `user_keys` table.
   - Enables `/identify` across all enrolled active `server_key` templates.

---

## 2. Endpoints Overview

| Method | Path | Auth | Content-Type | Description |
|---|---|---|---|---|
| `GET` | `/health` | Optional | `application/json` | System health, loaded model status, database connectivity, and parameter checksum. |
| `POST` | `/enroll` | Required | `multipart/form-data` | Enrolls a new user with 5 face images and 5 fingerprint impressions. |
| `POST` | `/verify` | Required | `multipart/form-data` | 1:1 biometric verification against claimed username. Rate limited. |
| `POST` | `/identify` | Required | `multipart/form-data` | 1:N biometric identification against active `server_key` templates. |
| `POST` | `/revoke` | Required | `application/x-www-form-urlencoded` | Revokes the active template and increments `key_version` for re-enrollment. |
| `GET` | `/users` | Required | `application/json` | Lists enrolled users (metadata only: username, key mode, version, creation timestamp). |
| `GET` | `/metrics/latest` | Required | `application/json` | Serves benchmark metrics and verification summary from `results/` for dashboard. |

---

## 3. Endpoint Details

### `GET /health`
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "models_loaded": true,
  "database": "connected",
  "public_parameters_sha256": "ded6e0b1163b7615a2c1895203fa73ba322d720e18c4858fd82413910671acaf"
}
```

### `POST /enroll`
- **Request Form Fields**:
  - `username` (string, 3-64 chars)
  - `key_mode` (`"user_secret"` | `"server_key"`, default `"user_secret"`)
  - `user_secret` (string, required if `key_mode="user_secret"`)
  - `face_images` (exactly 5 image files)
  - `finger_images` (exactly 5 image files)
- **Quality & Consistency Checks (FR-12)**:
  - Validates image decodability.
  - Computes pairwise cosine similarity against sample mean. Rejects enrollment if minimum face similarity $< 0.45$ or minimum fingerprint similarity $< 0.70$.
- **Response**: `200 OK`
```json
{
  "user_id": "8bb3d3a1-7788-4c8d-93cb-56e6d194c5e3",
  "username": "alice",
  "key_mode": "user_secret",
  "key_version": 1,
  "m": 512,
  "message": "User alice enrolled successfully"
}
```
- **Errors**: `400 Bad Request` (quality failure or count mismatch), `409 Conflict` (username already exists).

### `POST /verify`
- **Request Form Fields**:
  - `username` (string)
  - `user_secret` (string, required if `key_mode="user_secret"`)
  - `face_image` (single image file)
  - `finger_image` (single image file)
- **Rate Limiting & Lockout Defense (A6)**:
  - Tracks consecutive failed verification attempts per username.
  - Locks out username for 15 minutes after 5 consecutive failures.
- **Response**: `200 OK`
```json
{
  "match": true,
  "score": 0.1289,
  "threshold": 0.35,
  "key_version": 1,
  "message": "Verification successful"
}
```
- **Errors**: `401 Unauthorized` (bad API token), `403 Forbidden` (incorrect secret), `404 Not Found` (user not found), `429 Too Many Requests` (account locked out).

### `POST /identify`
- **Request Form Fields**:
  - `face_image` (single image file)
  - `finger_image` (single image file)
  - `top_k` (integer, default 5)
- **Behavior**:
  - Iterates over active `server_key` enrolled templates.
  - Computes normalized Hamming distance for each candidate.
  - Returns ranked list of candidates with score below $\tau = 0.35$.
- **Response**: `200 OK`
```json
{
  "candidates": [
    {"username": "bob", "score": 0.115, "rank": 1}
  ]
}
```

### `POST /revoke`
- **Request Form Fields**:
  - `username` (string)
- **Behavior**:
  - Sets `revoked_at = NOW()` on the user's active template.
  - Increments `key_version` so subsequent enrollments use fresh chaos parameters.
- **Response**: `200 OK`
```json
{
  "username": "alice",
  "revoked_key_version": 1,
  "new_key_version": 2,
  "message": "Template revoked successfully"
}
```

---

## 4. In-Memory Security & Lifecycle Guarantees

1. **No Disk Persistence**: Uploaded images are read into memory byte streams, decoded into tensors, and immediately unlinked/collected.
2. **Explicit Garbage Collection**: Endpoints execute inside `try ... finally` blocks invoking `gc.collect()` to minimize residency of raw feature vectors and image arrays.
3. **Audit Logging**: The `audit_log` records event types (`enroll`, `verify`, `identify`, `revoke`), status (`success`, `failure`, `lockout`, `rejected`), IP address, and score. **Zero biometric images, embeddings, fused vectors, or secret keys are ever logged**.
