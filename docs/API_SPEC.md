# API_SPEC.md (FastAPI, JSON + multipart)
Auth for the demo: static bearer token from env (`API_TOKEN`). Document that production would need real authN.

| Method | Path | Body | Response |
|---|---|---|---|
| GET | /health | - | `{status}` |
| POST | /enroll | form: `username`, `face_images[5]`, `finger_images[5]` | `{user_id, key_version, m}` |
| POST | /verify | form: `username`, `face_image`, `finger_image` | `{match: bool, score, threshold}` |
| POST | /identify | form: `face_image`, `finger_image`, `top_k` | `{candidates:[{user_id, score, rank}]}` |
| POST | /revoke | json: `{username}` | `{new_key_version}` (client then re-enrolls) |
| GET | /users | - | list (no biometric data) |
| GET | /metrics/latest | - | summary from `results/` for the dashboard |

Errors: 400 bad image / no face, 404 unknown user, 409 already enrolled, 422 validation.
Score = normalized Hamming distance (0 identical, ~0.5 unrelated).
All endpoints process images in memory only.
