"""src/api/main.py

FastAPI application for ZK-CaMBio Cancelable Multimodal Biometrics (Phase 7).
Implements:
- GET /health
- POST /enroll
- POST /verify
- POST /identify (server_key users only)
- POST /revoke
- GET /users
- GET /metrics/latest

Security & Design (D-016):
- In-memory processing only with explicit try/finally cleanup.
- Zero biometric or secret data in logs, audit tables, or response bodies.
- Two key modes: "user_secret" (default, zero key stored) and "server_key" (1:N identification).
- Rate-limiting & brute-force lockout counter per username (A6 defense).
- Bearer token authentication via API_TOKEN environment variable.
"""

from __future__ import annotations

import gc
import hmac
import json
import logging
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.service import BiometricService, validate_user_secret
from src.db.models import AuditLog, AuthRateLimit, Template, User, UserKey
from src.db.session import get_db, init_db
from src.fusion.fuse import fuse_embeddings_feature_level

# Configure privacy-preserving logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zkcambio.api")

# Static bearer token auth
API_TOKEN = os.environ.get("API_TOKEN", "zkcambio_dev_secret_token_2026")


def is_dev_mode() -> bool:
    """Returns true if dev mode is enabled via environment variable."""
    return os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")


def verify_bearer_token(authorization: Annotated[str | None, Header()] = None) -> None:
    """Validates authorization bearer token using timing-safe comparison."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if not hmac.compare_digest(token, API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )


def compute_lockout_delay(failed_count: int) -> int:
    """Computes escalating delay in seconds based on failed attempts:
    k < 3: 0
    k = 3: 2s
    k = 4: 5s
    k = 5: 15s
    k = 6: 30s
    k >= 7: min(60 * 2^(k-7), 300)s
    """
    if failed_count < 3:
        return 0
    if failed_count == 3:
        return 2
    if failed_count == 4:
        return 5
    if failed_count == 5:
        return 15
    if failed_count == 6:
        return 30
    return min(60 * (2 ** (failed_count - 7)), 300)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensures datetime is UTC timezone-aware for SQLite and Postgres compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def check_rate_limit_and_lockout(db: Session, username: str, ip_address: str | None) -> None:
    """Checks per-IP and per-username escalating delay from the database."""
    now = datetime.now(UTC)

    # 1. Check IP lockout first (protects server from distributed or single-source brute forcing)
    if ip_address:
        ip_rec = db.query(AuthRateLimit).filter(
            AuthRateLimit.identifier_type == "ip",
            AuthRateLimit.identifier_value == ip_address,
        ).first()
        if ip_rec:
            ip_locked = ensure_utc(ip_rec.locked_until)
            if ip_locked and now < ip_locked:
                wait_sec = max(1, int((ip_locked - now).total_seconds()) + 1)
                logger.warning("IP %s throttled due to repeated failures (%ds remaining)", ip_address, wait_sec)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts from your IP. Throttled for {wait_sec}s.",
                )

    # 2. Check per-username delay (escalating delay)
    user_rec = db.query(AuthRateLimit).filter(
        AuthRateLimit.identifier_type == "username",
        AuthRateLimit.identifier_value == username,
    ).first()
    if user_rec:
        user_locked = ensure_utc(user_rec.locked_until)
        if user_locked and now < user_locked:
            wait_sec = max(1, int((user_locked - now).total_seconds()) + 1)
            logger.warning("Account %s throttled due to repeated failures (%ds remaining)", username, wait_sec)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily delayed due to repeated failures. Retry in {wait_sec}s.",
            )



def record_failed_attempt(db: Session, username: str, ip_address: str | None) -> None:
    """Records failed attempt for username and IP, applying escalating delay."""
    now = datetime.now(UTC)

    # Update username record
    user_rec = db.query(AuthRateLimit).filter(
        AuthRateLimit.identifier_type == "username",
        AuthRateLimit.identifier_value == username,
    ).first()
    if not user_rec:
        user_rec = AuthRateLimit(
            identifier_type="username",
            identifier_value=username,
            failed_count=1,
            last_failed_at=now,
        )
        db.add(user_rec)
    else:
        user_rec.failed_count += 1
        user_rec.last_failed_at = now

    delay_user = compute_lockout_delay(user_rec.failed_count)
    user_rec.locked_until = (now + timedelta(seconds=delay_user)) if delay_user > 0 else None

    # Update IP record
    if ip_address:
        ip_rec = db.query(AuthRateLimit).filter(
            AuthRateLimit.identifier_type == "ip",
            AuthRateLimit.identifier_value == ip_address,
        ).first()
        if not ip_rec:
            ip_rec = AuthRateLimit(
                identifier_type="ip",
                identifier_value=ip_address,
                failed_count=1,
                last_failed_at=now,
            )
            db.add(ip_rec)
        else:
            ip_rec.failed_count += 1
            ip_rec.last_failed_at = now

        delay_ip = compute_lockout_delay(ip_rec.failed_count)
        ip_rec.locked_until = (now + timedelta(seconds=delay_ip)) if delay_ip > 0 else None

    db.commit()


def clear_failed_attempts(db: Session, username: str, ip_address: str | None) -> None:
    """Clears failed attempts on successful authentication for user and IP."""
    user_rec = db.query(AuthRateLimit).filter(
        AuthRateLimit.identifier_type == "username",
        AuthRateLimit.identifier_value == username,
    ).first()
    if user_rec:
        user_rec.failed_count = 0
        user_rec.locked_until = None

    if ip_address:
        ip_rec = db.query(AuthRateLimit).filter(
            AuthRateLimit.identifier_type == "ip",
            AuthRateLimit.identifier_value == ip_address,
        ).first()
        if ip_rec:
            ip_rec.failed_count = 0
            ip_rec.locked_until = None

    db.commit()



# Lifespan service management
service: BiometricService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Initializing BiometricService...")
    service = BiometricService()
    yield
    logger.info("Shutting down BiometricService...")
    service = None


app = FastAPI(
    title="ZK-CaMBio API",
    version="1.0.0",
    description="Cancelable Multimodal Biometrics API (Face + Fingerprint) via Integer Chaotic Hashing",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "zk-cambio-api", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/enroll")
async def enroll(
    username: Annotated[str, Form()],
    key_mode: Annotated[str, Form()] = "user_secret",
    user_secret: Annotated[str | None, Form()] = None,
    face_images: list[UploadFile] = File(...),
    finger_images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """Enrolls a new user with 5 face images and 5 fingerprint images."""
    if service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    # 1. Input validations
    if key_mode not in ("user_secret", "server_key"):
        raise HTTPException(status_code=400, detail="key_mode must be 'user_secret' or 'server_key'")
    if key_mode == "user_secret":
        try:
            validate_user_secret(user_secret)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e



    if len(face_images) != 5:
        raise HTTPException(status_code=400, detail=f"Exactly 5 face images required, got {len(face_images)}")
    if len(finger_images) != 5:
        raise HTTPException(status_code=400, detail=f"Exactly 5 fingerprint images required, got {len(finger_images)}")

    # Check if user already exists
    stmt = select(User).where(User.username == username)
    existing_user = db.execute(stmt).scalar_one_or_none()
    key_version = 1
    if existing_user is not None:
        stmt_active = select(Template).where(
            Template.user_id == existing_user.id,
            Template.revoked_at == None,  # noqa: E711
        )
        if db.execute(stmt_active).scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail=f"User '{username}' is already enrolled with an active template")
        stmt_latest = select(func.max(Template.key_version)).where(Template.user_id == existing_user.id)
        max_ver = db.execute(stmt_latest).scalar() or 1
        key_version = int(max_ver) + 1

    # 2. In-memory processing with explicit cleanup
    face_embs = []
    finger_embs = []
    try:
        for f_upload in face_images:
            content = await f_upload.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Face image exceeds 10MB limit")
            pil_img = service.decode_image_bytes(content, mode="RGB")
            emb = service.extract_face_embedding(pil_img)
            face_embs.append(emb)

        for g_upload in finger_images:
            content = await g_upload.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Fingerprint image exceeds 10MB limit")
            pil_img = service.decode_image_bytes(content, mode="L")
            emb = service.extract_finger_embedding(pil_img)
            finger_embs.append(emb)

        # 3. Quality & Consistency Checks (FR-12, Validation-Calibrated, >=3 consistent required)
        try:
            clean_face_embs, clean_finger_embs = service.filter_and_check_enrollment_quality(face_embs, finger_embs)
        except ValueError as qe:
            raise HTTPException(status_code=400, detail=f"Enrollment quality check failed: {qe}") from qe

        # 4. Multimodal Fusion (mean template across consistent impressions, >=3 required)
        face_tmpl = np.mean(clean_face_embs, axis=0)
        face_tmpl /= np.linalg.norm(face_tmpl)
        finger_tmpl = np.mean(clean_finger_embs, axis=0)
        finger_tmpl /= np.linalg.norm(finger_tmpl)

        fused_vec = fuse_embeddings_feature_level(face_tmpl, finger_tmpl, w=service.w)

        # 5. Database User Record & Per-User Salt (Phase 7d)
        if existing_user is None:
            user_record = User(
                id=uuid.uuid4(),
                username=username,
                key_mode=key_mode,
                kdf_salt=secrets.token_hex(16),
                active=True,
            )
            db.add(user_record)
            db.flush()
        else:
            user_record = existing_user
            user_record.active = True
            user_record.key_mode = key_mode
            if not user_record.kdf_salt:
                user_record.kdf_salt = secrets.token_hex(16)
            db.flush()

        # 6. Key Derivation & Cancelable Transformation (Binds user_id & per-user kdf_salt)
        state, r_param = service.derive_user_chaos_params(
            username=username,
            key_mode=key_mode,
            key_version=key_version,
            user_secret=user_secret,
            user_id=str(user_record.id),
            user_kdf_salt=user_record.kdf_salt,
        )
        template_bytes = service.generate_cancelable_template(fused_vec, state, r_param)

        new_template = Template(
            user_id=user_record.id,
            key_version=key_version,
            algo_version="zkcambio_v1",
            key_mode=key_mode,
            m=service.m,
            template=template_bytes,
        )
        db.add(new_template)

        # If server_key mode, persist server key
        if key_mode == "server_key":
            user_key_rec = UserKey(
                user_id=user_record.id,
                key_version=key_version,
                key_material=service.master_key,  # In production, wrapped with KMS
            )
            db.add(user_key_rec)

        # Audit log (no biometric data, no user secret)
        audit = AuditLog(
            user_id=user_record.id,
            event="enroll",
            key_mode=key_mode,
            result="success",
        )
        db.add(audit)
        db.commit()

        logger.info("Successfully enrolled user %s (key_mode=%s, version=%d)", username, key_mode, key_version)
        return {
            "user_id": str(user_record.id),
            "username": username,
            "key_mode": key_mode,
            "key_version": key_version,
            "m": service.m,
            "status": "enrolled",
        }

    finally:
        # Explicit cleanup of sensitive transient arrays from memory
        del face_embs
        del finger_embs
        gc.collect()


@app.post("/verify")
async def verify(
    request: Request,
    username: Annotated[str, Form()],
    user_secret: Annotated[str | None, Form()] = None,
    face_image: UploadFile = File(...),
    finger_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """Authenticates a user by matching probe biometrics against active cancelable template."""
    if service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    client_ip = request.headers.get("x-forwarded-for")
    if not client_ip and request.client:
        client_ip = request.client.host
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    check_rate_limit_and_lockout(db, username, client_ip)


    # 1. Fetch user and active template
    stmt_user = select(User).where(User.username == username, User.active == True)  # noqa: E712
    user = db.execute(stmt_user).scalar_one_or_none()
    if user is None:
        record_failed_attempt(db, username, client_ip)
        raise HTTPException(status_code=404, detail=f"User '{username}' not found or inactive")

    stmt_tmpl = select(Template).where(
        Template.user_id == user.id,
        Template.revoked_at == None,  # noqa: E711
    )
    tmpl_rec = db.execute(stmt_tmpl).scalar_one_or_none()
    if tmpl_rec is None:
        raise HTTPException(status_code=400, detail=f"No active template found for user '{username}'")

    if user.key_mode == "user_secret" and not user_secret:
        record_failed_attempt(db, username, client_ip)
        raise HTTPException(status_code=400, detail="user_secret is required for this user")

    # 2. Extract probe biometrics
    try:
        f_content = await face_image.read()
        g_content = await finger_image.read()

        face_pil = service.decode_image_bytes(f_content, mode="RGB")
        finger_pil = service.decode_image_bytes(g_content, mode="L")

        face_emb = service.extract_face_embedding(face_pil)
        finger_emb = service.extract_finger_embedding(finger_pil)

        probe_fused = fuse_embeddings_feature_level(face_emb, finger_emb, w=service.w)

        # 3. Derive key parameters & generate probe template (Binds user_id & per-user kdf_salt)
        try:
            state, r_param = service.derive_user_chaos_params(
                username=username,
                key_mode=user.key_mode,
                key_version=tmpl_rec.key_version,
                user_secret=user_secret,
                user_id=str(user.id),
                user_kdf_salt=user.kdf_salt,
            )
        except ValueError as e:
            record_failed_attempt(db, username, client_ip)
            raise HTTPException(status_code=400, detail=str(e)) from e


        probe_template = service.generate_cancelable_template(probe_fused, state, r_param)

        # 4. Hamming matching against enrolled template
        score = service.compute_hamming_distance(tmpl_rec.template, probe_template)
        is_match = bool(score <= service.tau_eer)

        # Audit log: hill-climbing defense: do NOT store score unless DEV_MODE=true
        dev = is_dev_mode()
        audit = AuditLog(
            user_id=user.id,
            event="verify",
            key_mode=user.key_mode,
            result="success" if is_match else "rejected",
            score=round(score, 4) if dev else None,
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()

        if is_match:
            clear_failed_attempts(db, username, client_ip)
            logger.info("Verification SUCCESS for %s", username)
        else:
            record_failed_attempt(db, username, client_ip)
            logger.info("Verification REJECTED for %s", username)

        response_payload: dict[str, Any] = {
            "match": is_match,
            "threshold": service.tau_eer,
            "key_version": tmpl_rec.key_version,
        }
        if dev:
            # Hill-climbing defense: return score ONLY when DEV_MODE=true
            response_payload["score"] = round(score, 4)
            response_payload["normalized_hamming_distance"] = round(score, 4)

        return response_payload

    finally:
        gc.collect()


@app.post("/identify")
async def identify(
    face_image: UploadFile = File(...),
    finger_image: UploadFile = File(...),
    top_k: Annotated[int, Form()] = 5,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """1:N Identification across 'server_key' users ONLY.

    Disabled for 'user_secret' users by design (D-016).
    """
    if service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    # Fetch active templates for server_key users
    stmt = (
        select(Template, User)
        .join(User, Template.user_id == User.id)
        .where(
            Template.key_mode == "server_key",
            Template.revoked_at == None,  # noqa: E711
            User.active == True,  # noqa: E712
        )
    )
    records = db.execute(stmt).all()
    if not records:
        return {"candidates": [], "message": "No enrolled server_key users available for identification"}

    try:
        f_content = await face_image.read()
        g_content = await finger_image.read()
        face_pil = service.decode_image_bytes(f_content, mode="RGB")
        finger_pil = service.decode_image_bytes(g_content, mode="L")
        face_emb = service.extract_face_embedding(face_pil)
        finger_emb = service.extract_finger_embedding(finger_pil)
        probe_fused = fuse_embeddings_feature_level(face_emb, finger_emb, w=service.w)

        dev = is_dev_mode()
        candidates = []
        for tmpl_rec, user_rec in records:
            state, r_param = service.derive_user_chaos_params(
                username=user_rec.username,
                key_mode="server_key",
                key_version=tmpl_rec.key_version,
            )
            probe_template = service.generate_cancelable_template(probe_fused, state, r_param)
            hd = service.compute_hamming_distance(tmpl_rec.template, probe_template)
            cand: dict[str, Any] = {
                "user_id": str(user_rec.id),
                "username": user_rec.username,
                "match": bool(hd <= service.tau_eer),
                "_internal_hd": hd,
            }
            if dev:
                cand["score"] = round(hd, 4)
            candidates.append(cand)

        candidates.sort(key=lambda c: c["_internal_hd"])
        top_candidates = candidates[:top_k]
        for rank, c in enumerate(top_candidates, start=1):
            c["rank"] = rank
            del c["_internal_hd"]

        return {"candidates": top_candidates}
    finally:
        gc.collect()



@app.post("/revoke")
def revoke(
    username: Annotated[str, Form()],
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """Revokes active cancelable template for a user and increments key version."""
    stmt_user = select(User).where(User.username == username)
    user = db.execute(stmt_user).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    stmt_tmpl = select(Template).where(
        Template.user_id == user.id,
        Template.revoked_at == None,  # noqa: E711
    )
    active_tmpls = db.execute(stmt_tmpl).scalars().all()
    if not active_tmpls:
        raise HTTPException(status_code=400, detail=f"No active templates found for user '{username}'")

    now = datetime.now(UTC)
    latest_version = 1
    for tmpl in active_tmpls:
        tmpl.revoked_at = now
        latest_version = max(latest_version, tmpl.key_version)

    # Regenerate per-user KDF salt on revoke to guarantee key separation
    user.kdf_salt = secrets.token_hex(16)

    # If server_key mode, also revoke user_keys record
    stmt_key = select(UserKey).where(UserKey.user_id == user.id, UserKey.revoked_at == None)  # noqa: E711
    active_keys = db.execute(stmt_key).scalars().all()
    for uk in active_keys:
        uk.revoked_at = now

    audit = AuditLog(
        user_id=user.id,
        event="revoke",
        key_mode=user.key_mode,
        result="success",
    )
    db.add(audit)
    db.commit()

    logger.info("Revoked template for user %s. New version available: %d", username, latest_version + 1)
    return {
        "user_id": str(user.id),
        "username": username,
        "revoked_version": latest_version,
        "new_key_version": latest_version + 1,
        "status": "revoked",
    }


@app.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
) -> list[dict[str, Any]]:
    """Returns non-sensitive user directory."""
    stmt = select(User).order_by(User.created_at)
    users = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "key_mode": u.key_mode,
            "active": u.active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@app.get("/metrics/latest")
def get_latest_metrics(_: None = Depends(verify_bearer_token)) -> dict[str, Any]:
    """Returns latest benchmark metrics from results/ for dashboard display."""
    cancelable_path = Path("results/cancelable_eer.json")
    security_path = Path("results/security_eval.json")
    fused_path = Path("results/fused_unprotected.json")

    metrics: dict[str, Any] = {}
    if cancelable_path.is_file():
        with open(cancelable_path, encoding="utf-8") as f:
            metrics["cancelable"] = json.load(f)
    if security_path.is_file():
        with open(security_path, encoding="utf-8") as f:
            metrics["security"] = json.load(f)
    if fused_path.is_file():
        with open(fused_path, encoding="utf-8") as f:
            metrics["fused_unprotected"] = json.load(f)

    return metrics
