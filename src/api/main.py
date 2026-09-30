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
import json
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import UTC, datetime
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
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.service import BiometricService
from src.db.models import AuditLog, Template, User, UserKey
from src.db.session import get_db, init_db
from src.fusion.fuse import fuse_embeddings_feature_level

# Configure privacy-preserving logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zkcambio.api")

# Static bearer token auth
API_TOKEN = os.environ.get("API_TOKEN", "zkcambio_dev_secret_token_2026")


def verify_bearer_token(authorization: Annotated[str | None, Header()] = None) -> None:
    """Validates authorization bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )


# Rate limiting & Lockout tracker (A6 mitigation)
# Tracks failed attempts per username within window
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SEC = 60
FAILED_ATTEMPTS: dict[str, list[float]] = defaultdict(list)


def check_rate_limit_and_lockout(username: str) -> None:
    now = time.time()
    attempts = FAILED_ATTEMPTS[username]
    # Filter attempts within lockout duration
    recent = [t for t in attempts if now - t < LOCKOUT_DURATION_SEC]
    FAILED_ATTEMPTS[username] = recent
    if len(recent) >= MAX_FAILED_ATTEMPTS:
        logger.warning("Account %s locked out due to excessive failed attempts", username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts for {username}. Account temporarily locked out.",
        )


def record_failed_attempt(username: str) -> None:
    FAILED_ATTEMPTS[username].append(time.time())


def clear_failed_attempts(username: str) -> None:
    if username in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[username]


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
    if key_mode == "user_secret" and not user_secret:
        raise HTTPException(status_code=400, detail="user_secret is required for 'user_secret' mode")

    if len(face_images) != 5:
        raise HTTPException(status_code=400, detail=f"Exactly 5 face images required, got {len(face_images)}")
    if len(finger_images) != 5:
        raise HTTPException(status_code=400, detail=f"Exactly 5 fingerprint images required, got {len(finger_images)}")

    # Check if user already exists
    stmt = select(User).where(User.username == username)
    existing_user = db.execute(stmt).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail=f"User '{username}' is already enrolled")

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

        # 3. Quality & Consistency Checks (FR-12)
        try:
            service.check_enrollment_quality(face_embs, finger_embs)
        except ValueError as qe:
            raise HTTPException(status_code=400, detail=f"Enrollment quality check failed: {qe}") from qe

        # 4. Multimodal Fusion (mean template across 5 impressions)
        face_tmpl = np.mean(face_embs, axis=0)
        face_tmpl /= np.linalg.norm(face_tmpl)
        finger_tmpl = np.mean(finger_embs, axis=0)
        finger_tmpl /= np.linalg.norm(finger_tmpl)

        fused_vec = fuse_embeddings_feature_level(face_tmpl, finger_tmpl, w=service.w)

        # 5. Key Derivation & Cancelable Transformation
        key_version = 1
        state, r_param = service.derive_user_chaos_params(
            username=username,
            key_mode=key_mode,
            key_version=key_version,
            user_secret=user_secret,
        )
        template_bytes = service.generate_cancelable_template(fused_vec, state, r_param)

        # 6. Database Storage (Users & Templates ONLY; NO keys for user_secret mode)
        new_user = User(username=username, key_mode=key_mode, active=True)
        db.add(new_user)
        db.flush()

        new_template = Template(
            user_id=new_user.id,
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
                user_id=new_user.id,
                key_version=key_version,
                key_material=service.master_key,  # In production, wrapped with KMS
            )
            db.add(user_key_rec)

        # Audit log (no biometric data, no user secret)
        audit = AuditLog(
            user_id=new_user.id,
            event="enroll",
            key_mode=key_mode,
            result="success",
        )
        db.add(audit)
        db.commit()

        logger.info("Successfully enrolled user %s (key_mode=%s)", username, key_mode)
        return {
            "user_id": str(new_user.id),
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

    check_rate_limit_and_lockout(username)

    # 1. Fetch user and active template
    stmt_user = select(User).where(User.username == username, User.active == True)  # noqa: E712
    user = db.execute(stmt_user).scalar_one_or_none()
    if user is None:
        record_failed_attempt(username)
        raise HTTPException(status_code=404, detail=f"User '{username}' not found or inactive")

    stmt_tmpl = select(Template).where(
        Template.user_id == user.id,
        Template.revoked_at == None,  # noqa: E711
    )
    tmpl_rec = db.execute(stmt_tmpl).scalar_one_or_none()
    if tmpl_rec is None:
        raise HTTPException(status_code=400, detail=f"No active template found for user '{username}'")

    if user.key_mode == "user_secret" and not user_secret:
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

        # 3. Derive key parameters & generate probe template
        state, r_param = service.derive_user_chaos_params(
            username=username,
            key_mode=user.key_mode,
            key_version=tmpl_rec.key_version,
            user_secret=user_secret,
        )
        probe_template = service.generate_cancelable_template(probe_fused, state, r_param)

        # 4. Hamming matching against enrolled template
        score = service.compute_hamming_distance(tmpl_rec.template, probe_template)
        is_match = bool(score <= service.tau_eer)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            event="verify",
            key_mode=user.key_mode,
            result="success" if is_match else "rejected",
            score=score,
        )
        db.add(audit)
        db.commit()

        if is_match:
            clear_failed_attempts(username)
            logger.info("Verification SUCCESS for %s (HD=%.4f <= %.4f)", username, score, service.tau_eer)
        else:
            record_failed_attempt(username)
            logger.info("Verification REJECTED for %s (HD=%.4f > %.4f)", username, score, service.tau_eer)

        return {
            "match": is_match,
            "normalized_hamming_distance": round(score, 4),
            "threshold": service.tau_eer,
            "key_version": tmpl_rec.key_version,
        }

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

        candidates = []
        for tmpl_rec, user_rec in records:
            state, r_param = service.derive_user_chaos_params(
                username=user_rec.username,
                key_mode="server_key",
                key_version=tmpl_rec.key_version,
            )
            probe_template = service.generate_cancelable_template(probe_fused, state, r_param)
            hd = service.compute_hamming_distance(tmpl_rec.template, probe_template)
            candidates.append(
                {
                    "user_id": str(user_rec.id),
                    "username": user_rec.username,
                    "score": round(hd, 4),
                    "match": bool(hd <= service.tau_eer),
                }
            )

        candidates.sort(key=lambda c: c["score"])
        top_candidates = candidates[:top_k]
        for rank, c in enumerate(top_candidates, start=1):
            c["rank"] = rank

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
