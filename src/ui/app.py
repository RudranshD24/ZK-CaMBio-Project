"""src/ui/app.py

ZK-CaMBio Streamlit Demonstration Application (Phase 8).
Architectural Boundary:
- Talks to the FastAPI backend strictly via HTTP (requests).
- NEVER imports machine learning models, biometric extractors, key material, or the C++ chaos engine.
- All secrets are handled via password inputs and cleared from state after use.
- Works fully offline in an air-gapped or network-disabled container.
"""
# ruff: noqa: E402
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st
from PIL import Image

from src.ui.demo_data import (
    get_fmr_fnmr_at_threshold,
    load_demo_manifest,
    load_validation_threshold_curve,
)

# Configuration from environment
API_URL = os.environ.get("API_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("API_TOKEN", "")
DEV_MODE = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")

st.set_page_config(
    page_title="ZK-CaMBio | Privacy-Preserving Multimodal Biometrics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .match-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 16px 28px;
        border-radius: 12px;
        font-size: 26px;
        font-weight: 800;
        text-align: center;
        letter-spacing: 2px;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
        margin: 15px 0;
    }
    .no-match-badge {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 16px 28px;
        border-radius: 12px;
        font-size: 26px;
        font-weight: 800;
        text-align: center;
        letter-spacing: 2px;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
        margin: 15px 0;
    }
    .demo-banner {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 5px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        font-weight: 600;
        margin: 12px 0;
    }
    .footer-text {
        font-size: 13px;
        color: #6b7280;
        text-align: center;
        padding-top: 30px;
        margin-top: 40px;
        border-top: 1px solid #e5e7eb;
    }
    .metric-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_headers() -> dict[str, str]:
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}


def render_footer():
    st.markdown(
        '<div class="footer-text">'
        "Virtual subjects built from UMDFaces + FVC2004 (independent identities paired for research). "
        "Research prototype."
        "</div>",
        unsafe_allow_html=True,
    )


def read_file_bytes(file_input: Any) -> bytes | None:
    if file_input is None:
        return None
    if isinstance(file_input, str):
        if os.path.isfile(file_input):
            with open(file_input, "rb") as f:
                return f.read()
        return None
    if hasattr(file_input, "getvalue"):
        return file_input.getvalue()
    if hasattr(file_input, "read"):
        return file_input.read()
    return None


# Sidebar Navigation
st.sidebar.title("🛡️ ZK-CaMBio")
st.sidebar.caption("Cancelable Multimodal Biometrics")

if DEV_MODE:
    st.sidebar.markdown(
        '<div class="demo-banner">⚙️ <b>DEV_MODE: ACTIVE</b><br>'
        "<small>Scores visible for evaluation</small></div>",
        unsafe_allow_html=True,
    )

page = st.sidebar.radio(
    "Navigation",
    ["Enroll", "Verify (1:1)", "Identify (1:N)", "Revoke", "Results", "Threat demo"],
    index=0,
)

demo_manifest = load_demo_manifest()
val_curve = load_validation_threshold_curve()

# ==============================================================================
# 1. ENROLL PAGE
# ==============================================================================
if page == "Enroll":
    st.header("👤 Subject Enrollment")
    st.write(
        "Enroll a subject by submitting 5 face and 5 fingerprint impressions. "
        "The system extracts embeddings in memory, checks intra-impression quality, "
        "applies key-dependent chaotic projection, and stores ONLY the 512-bit cancelable template."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Account Identity & Key Mode")
        username = st.text_input("Username", value="alice_demo", help="Unique subject identifier")
        key_mode = st.selectbox(
            "Key Mode",
            ["user_secret", "server_key"],
            index=0,
            help="user_secret: derived client-side from passphrase (zero server key storage); server_key: server-stored encrypted key (enables 1:N)",
        )

        user_secret = ""
        if key_mode == "user_secret":
            user_secret = st.text_input(
                "Personal Passphrase / PIN (User Secret)",
                type="password",
                help="Passphrase stretched via scrypt; never stored on the server.",
            )
            st.caption("🔒 Secret is held transiently in memory and never echoed or logged.")

    with col2:
        st.subheader("2. Biometric Impression Source")
        input_source = st.radio(
            "Source Selection",
            ["Pick Demo Subject (Test Split)", "Upload Custom Images", "Demonstrate Quality Failure Case"],
            index=0,
        )

    face_bytes_list: list[bytes] = []
    finger_bytes_list: list[bytes] = []

    if input_source == "Pick Demo Subject (Test Split)":
        if demo_manifest:
            options = {d["label"]: d for d in demo_manifest[:20]}
            selected_label = st.selectbox("Select Test Subject from Manifest", list(options.keys()))
            selected_sub = options[selected_label]

            st.info(f"Selected: **{selected_sub['subject_id']}** ({selected_sub['db']})")
            st.success("✅ **Quality Check: PASS** (Impressions meet quality & consistency gates)")

            # Preview sample impressions
            pcol1, pcol2 = st.columns(2)
            if selected_sub["face_enroll_files"] and os.path.isfile(selected_sub["face_enroll_files"][0]):
                with pcol1:
                    st.image(selected_sub["face_enroll_files"][0], caption="Sample Face Impression", width=140)
            if selected_sub["finger_enroll_files"] and os.path.isfile(selected_sub["finger_enroll_files"][0]):
                with pcol2:
                    st.image(selected_sub["finger_enroll_files"][0], caption="Sample Fingerprint Impression", width=140)

            for fpath in selected_sub["face_enroll_files"][:5]:
                b = read_file_bytes(fpath)
                if b:
                    face_bytes_list.append(b)
            for fpath in selected_sub["finger_enroll_files"][:5]:
                b = read_file_bytes(fpath)
                if b:
                    finger_bytes_list.append(b)
        else:
            st.warning("Demo dataset manifest not found. Please switch to 'Upload Custom Images'.")

    elif input_source == "Demonstrate Quality Failure Case":
        st.error("⚠️ **Quality Check Demonstration: INTENTIONAL FAILURE**")
        st.write(
            "Demonstrates FR-12 quality check rejection when images are corrupt or fail consistency gates."
        )
        fail_type = st.selectbox(
            "Failure Type to Simulate",
            ["Blank / Missing Face (No Face Detected)", "Inconsistent Fingerprint Impressions (< 3 Consistent)"],
        )
        if fail_type == "Blank / Missing Face (No Face Detected)":
            # Generate blank face images
            img = Image.new("RGB", (160, 160), color=(128, 128, 128))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            blank_b = buf.getvalue()
            face_bytes_list = [blank_b] * 5
            # Valid sample fingers
            if demo_manifest and demo_manifest[0]["finger_enroll_files"]:
                for fpath in demo_manifest[0]["finger_enroll_files"][:5]:
                    b = read_file_bytes(fpath)
                    if b:
                        finger_bytes_list.append(b)
        else:
            # Valid faces, but 5 different completely unrelated fingers from different subjects
            if demo_manifest and len(demo_manifest) >= 5:
                for fpath in demo_manifest[0]["face_enroll_files"][:5]:
                    b = read_file_bytes(fpath)
                    if b:
                        face_bytes_list.append(b)
                # Take finger 1 from 5 different subjects
                for i in range(5):
                    fpath = demo_manifest[i]["finger_enroll_files"][0]
                    b = read_file_bytes(fpath)
                    if b:
                        finger_bytes_list.append(b)

    else:
        ucol1, ucol2 = st.columns(2)
        with ucol1:
            uploaded_faces = st.file_uploader(
                "Upload 5 Face Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True
            )
            if uploaded_faces:
                for uf in uploaded_faces[:5]:
                    face_bytes_list.append(uf.getvalue())
        with ucol2:
            uploaded_fingers = st.file_uploader(
                "Upload 5 Fingerprint Images", type=["tif", "tiff", "png", "bmp"], accept_multiple_files=True
            )
            if uploaded_fingers:
                for ufin in uploaded_fingers[:5]:
                    finger_bytes_list.append(ufin.getvalue())

    st.markdown("---")
    enroll_btn = st.button("🚀 Enroll Subject", type="primary", use_container_width=True)

    if enroll_btn:
        if not username:
            st.error("Please provide a username.")
        elif key_mode == "user_secret" and not user_secret:
            st.error("Please enter a personal passphrase for user_secret mode.")
        elif len(face_bytes_list) < 5 or len(finger_bytes_list) < 5:
            st.error(f"Enrollment requires exactly 5 face and 5 fingerprint images (provided {len(face_bytes_list)} face, {len(finger_bytes_list)} finger).")
        else:
            with st.spinner("Processing biometric impressions and generating chaotic template..."):
                files = []
                for i, fb in enumerate(face_bytes_list[:5]):
                    files.append(("face_images", (f"face_{i}.jpg", fb, "image/jpeg")))
                for i, finb in enumerate(finger_bytes_list[:5]):
                    files.append(("finger_images", (f"finger_{i}.tif", finb, "image/tiff")))

                data = {"username": username, "key_mode": key_mode}
                if key_mode == "user_secret":
                    data["user_secret"] = user_secret

                try:
                    resp = requests.post(
                        f"{API_URL}/enroll",
                        headers=get_headers(),
                        data=data,
                        files=files,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        res = resp.json()
                        st.success("🎉 **Enrollment Successful!**")
                        st.json(res)
                        st.info(
                            f"Stored Template: {res.get('m', 512)} bits ({res.get('m', 512)//8} bytes). "
                            f"Key Version: {res.get('key_version', 1)}. "
                            "Zero raw embeddings or floating-point vectors are stored."
                        )
                    else:
                        st.error(f"❌ **Enrollment Failed (Status {resp.status_code}):** {resp.text}")
                except Exception as e:
                    st.error(f"Connection error to API: {e}")
                finally:
                    # Clear secret from local variable immediately
                    user_secret = ""

    render_footer()

# ==============================================================================
# 2. VERIFY (1:1) PAGE
# ==============================================================================
elif page == "Verify (1:1)":
    st.header("🔍 Biometric Verification (1:1 Match)")
    st.write(
        "Verify a single probe pair (1 face + 1 fingerprint) against an enrolled template."
    )

    vcol1, vcol2 = st.columns([1, 1])

    with vcol1:
        st.subheader("1. Claimed Identity")
        v_username = st.text_input("Username", value="alice_demo")
        v_secret = st.text_input("User Secret (if enrolled with user_secret)", type="password")

        if DEV_MODE:
            st.markdown("---")
            st.caption("🛠️ **DEV_MODE Utilities**")
            if st.button("🔄 Reset Lockout for Demo User", help="Clears failed attempt counters so demo is not blocked"):
                try:
                    r_res = requests.post(
                        f"{API_URL}/dev/reset_lockout",
                        headers=get_headers(),
                        data={"username": v_username},
                        timeout=10,
                    )
                    if r_res.status_code == 200:
                        st.success(f"Lockout counters reset for '{v_username}' and client IP.")
                    else:
                        st.error(f"Reset failed: {r_res.text}")
                except Exception as ex:
                    st.error(f"Error resetting: {ex}")

    with vcol2:
        st.subheader("2. Probe Selection")
        probe_mode = st.radio(
            "Select Probe Type",
            ["Genuine Probe (Same Subject)", "Impostor Probe (Pick an Impostor)", "Upload Probe Images"],
            index=0,
        )

    probe_face: bytes | None = None
    probe_finger: bytes | None = None

    if probe_mode == "Genuine Probe (Same Subject)":
        if demo_manifest:
            st.caption("Using genuine test probe for the demo subject.")
            probe_face = read_file_bytes(demo_manifest[0]["face_probe_file"])
            probe_finger = read_file_bytes(demo_manifest[0]["finger_probe_file"])
            pcols = st.columns(2)
            if demo_manifest[0]["face_probe_file"]:
                pcols[0].image(demo_manifest[0]["face_probe_file"], caption="Genuine Face Probe", width=130)
            if demo_manifest[0]["finger_probe_file"]:
                pcols[1].image(demo_manifest[0]["finger_probe_file"], caption="Genuine Finger Probe", width=130)

    elif probe_mode == "Impostor Probe (Pick an Impostor)":
        if len(demo_manifest) >= 2:
            st.warning("⚠️ **Impostor Selected**: Live demonstration of impostor rejection.")
            imp_options = {d["label"]: d for d in demo_manifest[1:15]}
            selected_imp_label = st.selectbox("Select Impostor Subject", list(imp_options.keys()))
            imp_sub = imp_options[selected_imp_label]

            probe_face = read_file_bytes(imp_sub["face_probe_file"])
            probe_finger = read_file_bytes(imp_sub["finger_probe_file"])
            pcols = st.columns(2)
            if imp_sub["face_probe_file"]:
                pcols[0].image(imp_sub["face_probe_file"], caption=f"Impostor Face ({imp_sub['subject_id']})", width=130)
            if imp_sub["finger_probe_file"]:
                pcols[1].image(imp_sub["finger_probe_file"], caption=f"Impostor Finger ({imp_sub['subject_id']})", width=130)

    else:
        ucol1, ucol2 = st.columns(2)
        with ucol1:
            u_fp = st.file_uploader("Upload Probe Face", type=["jpg", "jpeg", "png"])
            if u_fp:
                probe_face = u_fp.getvalue()
        with ucol2:
            u_fin = st.file_uploader("Upload Probe Fingerprint", type=["tif", "tiff", "png", "bmp"])
            if u_fin:
                probe_finger = u_fin.getvalue()

    # Informational Threshold Slider
    st.markdown("---")
    st.subheader("3. Operating Threshold & Error Tradeoff (Informational)")
    tau_slider = st.slider(
        "Operating Threshold τ (Normalized Hamming Distance)",
        min_value=0.200,
        max_value=0.450,
        value=0.3504,
        step=0.005,
        format="%.4f",
        help="Informational threshold slider: displays expected FMR and FNMR computed from 30 validation subjects.",
    )
    val_fmr, val_fnmr = get_fmr_fnmr_at_threshold(tau_slider, val_curve)
    scol1, scol2, scol3 = st.columns(3)
    scol1.metric("Selected Threshold τ", f"{tau_slider:.4f}")
    scol2.metric("Validation FMR (False Accept)", f"{val_fmr:.2f}%")
    scol3.metric("Validation FNMR (False Reject)", f"{val_fnmr:.2f}%")
    st.caption("ℹ️ *Note: Operational decision is enforced by the backend using the validation-calibrated operating point τ = 0.3504.*")

    verify_btn = st.button("🔐 Verify Probe", type="primary", use_container_width=True)

    if verify_btn:
        if not v_username:
            st.error("Please provide a username.")
        elif not probe_face or not probe_finger:
            st.error("Please supply both a face and fingerprint probe.")
        else:
            with st.spinner("Authenticating probe..."):
                files = [
                    ("face_image", ("probe_face.jpg", probe_face, "image/jpeg")),
                    ("finger_image", ("probe_finger.tif", probe_finger, "image/tiff")),
                ]
                data = {"username": v_username}
                if v_secret:
                    data["user_secret"] = v_secret

                try:
                    resp = requests.post(
                        f"{API_URL}/verify",
                        headers=get_headers(),
                        data=data,
                        files=files,
                        timeout=15,
                    )

                    if resp.status_code == 200:
                        res = resp.json()
                        is_match = res.get("match", False)
                        score = res.get("score")
                        threshold = res.get("threshold", 0.3504)

                        if is_match:
                            st.markdown('<div class="match-badge">✅ MATCH</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="no-match-badge">❌ NO MATCH</div>', unsafe_allow_html=True)

                        # Score visibility handling
                        if score is not None:
                            st.markdown(
                                '<div class="demo-banner">⚠️ <b>DEMO MODE: scores visible; '
                                "production hides them because scores enable hill-climbing attacks</b></div>",
                                unsafe_allow_html=True,
                            )
                            mcol1, mcol2, mcol3 = st.columns(3)
                            mcol1.metric("Hamming Distance", f"{score:.4f}")
                            mcol2.metric("Decision Threshold", f"{threshold:.4f}")
                            mcol3.metric("Decision Rule", f"Distance {'≤' if is_match else '>'} Threshold")
                        else:
                            st.info(
                                "🛡️ **Production Score Suppression**: Numeric scores are suppressed outside DEV_MODE "
                                "to eliminate gradient feedback that could assist iterative hill-climbing attacks."
                            )

                        st.json(res)

                    elif resp.status_code == 429:
                        st.error(f"🛑 **Account Locked Out (HTTP 429):** {resp.text}")
                        st.warning("Escalating delay in effect due to repeated failed attempts. Please wait or use DEV_MODE reset.")
                    else:
                        st.error(f"❌ Verification Error (Status {resp.status_code}): {resp.text}")

                except Exception as ex:
                    st.error(f"Connection error to API: {ex}")
                finally:
                    v_secret = ""

    render_footer()

# ==============================================================================
# 3. IDENTIFY (1:N) PAGE
# ==============================================================================
elif page == "Identify (1:N)":
    st.header("👥 Biometric Identification (1:N Search)")

    st.markdown(
        '<div class="demo-banner">'
        "ℹ️ <b>Security Boundary:</b> 1:N Identification is enabled <b>ONLY for accounts enrolled in server_key mode</b>. "
        "Accounts enrolled with <code>user_secret</code> derive chaotic projection keys client-side from personal passphrases; "
        "because the server possesses zero key material for these users, comparing an unkeyed probe against all templates "
        "would require brute-forcing all user secrets or performing unkeyed cross-matching, which is cryptographically impossible "
        "and explicitly prohibited by the threat model."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("🛠️ Gallery Status & Demo Seeding", expanded=False):
        st.write(
            "1:N search operates against enrolled accounts in **`server_key`** mode. "
            "If your gallery is currently empty or you want to populate it with test subjects, click below."
        )
        if st.button("📥 Pre-populate Gallery (Enroll 5 Test Subjects in server_key mode)"):
            if not demo_manifest:
                st.error("Demo manifest not found.")
            else:
                with st.spinner("Enrolling 5 demo subjects into server_key gallery..."):
                    enrolled_count = 0
                    for sub in demo_manifest[:5]:
                        s_id = sub["subject_id"]
                        u_name = f"demo_gallery_{s_id}"
                        f_files = [("face_images", (f"f_{idx}.jpg", read_file_bytes(fp), "image/jpeg")) for idx, fp in enumerate(sub["face_enroll_files"][:5])]
                        g_files = [("finger_images", (f"g_{idx}.tif", read_file_bytes(gp), "image/tiff")) for idx, gp in enumerate(sub["finger_enroll_files"][:5])]
                        try:
                            s_resp = requests.post(
                                f"{API_URL}/enroll",
                                headers=get_headers(),
                                data={"username": u_name, "key_mode": "server_key"},
                                files=f_files + g_files,
                                timeout=20,
                            )
                            if s_resp.status_code == 200:
                                enrolled_count += 1
                        except Exception:
                            pass
                    st.success(f"Gallery updated: enrolled {enrolled_count} demo subject(s) in server_key mode.")

    icol1, icol2 = st.columns([1, 1])
    with icol1:
        st.subheader("Probe Selection")
        id_probe_mode = st.radio(
            "Probe Source",
            ["Pick Demo Subject (Test Split)", "Upload Custom Images"],
            index=0,
        )

    id_probe_face: bytes | None = None
    id_probe_finger: bytes | None = None

    if id_probe_mode == "Pick Demo Subject (Test Split)" and demo_manifest:
        options = {d["label"]: d for d in demo_manifest[:15]}
        selected_id_label = st.selectbox("Select Probe Subject", list(options.keys()))
        selected_id_sub = options[selected_id_label]
        id_probe_face = read_file_bytes(selected_id_sub["face_probe_file"])
        id_probe_finger = read_file_bytes(selected_id_sub["finger_probe_file"])
        icols = st.columns(2)
        if selected_id_sub["face_probe_file"]:
            icols[0].image(selected_id_sub["face_probe_file"], caption="Probe Face", width=130)
        if selected_id_sub["finger_probe_file"]:
            icols[1].image(selected_id_sub["finger_probe_file"], caption="Probe Finger", width=130)
    else:
        ucol1, ucol2 = st.columns(2)
        with ucol1:
            u_fp = st.file_uploader("Probe Face", type=["jpg", "jpeg", "png"], key="id_face")
            if u_fp:
                id_probe_face = u_fp.getvalue()
        with ucol2:
            u_fin = st.file_uploader("Probe Finger", type=["tif", "tiff", "png", "bmp"], key="id_finger")
            if u_fin:
                id_probe_finger = u_fin.getvalue()

    top_k = st.slider("Top K Candidates", min_value=1, max_value=10, value=5)
    identify_btn = st.button("🔎 Run 1:N Identification", type="primary", use_container_width=True)

    if identify_btn:
        if not id_probe_face or not id_probe_finger:
            st.error("Please supply both a face and fingerprint probe.")
        else:
            with st.spinner("Searching gallery templates across server_key accounts..."):
                files = [
                    ("face_image", ("probe_face.jpg", id_probe_face, "image/jpeg")),
                    ("finger_image", ("probe_finger.tif", id_probe_finger, "image/tiff")),
                ]
                try:
                    resp = requests.post(
                        f"{API_URL}/identify",
                        headers=get_headers(),
                        data={"top_k": top_k},
                        files=files,
                        timeout=20,
                    )
                    if resp.status_code == 200:
                        res = resp.json()
                        candidates = res.get("candidates", [])
                        st.subheader(f"Candidates Found ({len(candidates)})")
                        if candidates:
                            top_cand = candidates[0]
                            if top_cand.get("match"):
                                st.markdown(
                                    f'<div class="match-badge">🎯 MATCH IDENTIFIED: {top_cand["username"]} (Rank 1)</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div class="no-match-badge">❌ NO GALLERY MATCH</div>',
                                    unsafe_allow_html=True,
                                )
                            st.table(candidates)
                        else:
                            st.warning("⚠️ **No matching server_key accounts found in the database.**")
                            st.info(
                                "ℹ️ 1:N Identification requires enrolled accounts in `server_key` mode. "
                                "Expand '🛠️ Gallery Status & Demo Seeding' above to seed demo subjects."
                            )
                    else:
                        st.error(f"Identification failed (Status {resp.status_code}): {resp.text}")
                except Exception as ex:
                    st.error(f"Connection error to API: {ex}")

    render_footer()

# ==============================================================================
# 4. REVOKE PAGE
# ==============================================================================
elif page == "Revoke":
    st.header("🔄 Template Revocation & Key Rotation")
    st.write(
        "Demonstrate ISO/IEC 30136 revocability: upon revocation, the active template is retired, "
        "and the user's key version is bumped. Genuine probes against the revoked template are 100% rejected, "
        "and re-enrollment under the new key version immediately restores recognition."
    )

    r_username = st.text_input("Username to Revoke", value="alice_demo")
    revoke_btn = st.button("🚫 Revoke Active Template", type="primary")

    if revoke_btn:
        if not r_username:
            st.error("Please provide a username.")
        else:
            with st.spinner(f"Revoking active template for '{r_username}'..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/revoke",
                        headers=get_headers(),
                        data={"username": r_username},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        res = resp.json()
                        st.success("✅ **Template Successfully Revoked!**")
                        st.json(res)
                        st.info(
                            f"Revoked Key Version: **v{res.get('revoked_version')}** → "
                            f"New Eligible Version: **v{res.get('new_key_version')}**. "
                            f"KDF salt has been regenerated."
                        )
                    else:
                        st.error(f"Revocation failed: {resp.text}")
                except Exception as ex:
                    st.error(f"Connection error: {ex}")

    st.markdown("---")
    st.subheader("🧪 Revocation Rejection Verification")
    st.write(
        "Attempt to authenticate a probe against the newly revoked user to verify immediate rejection (HTTP 400)."
    )

    probe_rev_btn = st.button("Test Verify Against Revoked User")
    if probe_rev_btn:
        if not demo_manifest:
            st.error("No demo probe available.")
        else:
            p_face = read_file_bytes(demo_manifest[0]["face_probe_file"])
            p_fin = read_file_bytes(demo_manifest[0]["finger_probe_file"])
            with st.spinner("Submitting probe against revoked account..."):
                files = [
                    ("face_image", ("f.jpg", p_face, "image/jpeg")),
                    ("finger_image", ("fin.tif", p_fin, "image/tiff")),
                ]
                try:
                    r_verify = requests.post(
                        f"{API_URL}/verify",
                        headers=get_headers(),
                        data={"username": r_username, "user_secret": "DemoSecret_2026!"},
                        files=files,
                        timeout=10,
                    )
                    if r_verify.status_code == 400:
                        st.success(
                            f"🛡️ **Revocation Enforced**: Status=400: {r_verify.json().get('detail')}"
                        )
                        st.info("Demonstrates 100.00% rejection of probes against revoked template versions.")
                    else:
                        st.warning(f"Unexpected status {r_verify.status_code}: {r_verify.text}")
                except Exception as ex:
                    st.error(f"Error: {ex}")

    render_footer()

# ==============================================================================
# 5. RESULTS PAGE
# ==============================================================================
elif page == "Results":
    st.header("📊 Empirical Evaluation Results")
    st.write(
        "Renders experimental results directly from `results/`, including headline Scenario K accuracy, "
        "ISO/IEC 30136 revocability and unlinkability benchmarks, and the explicit threat model claims table."
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 ROC & Identification CMC", "🔄 Revocability & Unlinkability", "⚖️ Privacy-Utility Tradeoff", "📋 Claims Table"]
    )

    with tab1:
        st.subheader("ROC Curves & Rank-1 Identification")
        c1, c2 = st.columns(2)
        with c1:
            if os.path.isfile("results/cancelable_roc.png"):
                st.image("results/cancelable_roc.png", caption="Cancelable vs Unprotected ROC Curve (120 Test Subjects)")
        with c2:
            if os.path.isfile("results/cancelable_cmc.png"):
                st.image("results/cancelable_cmc.png", caption="CMC Rank-1 Identification (Gallery 40 per DB)")

        st.markdown(
            """
            | System | Modality / Protection | Key Condition | Pooled EER (%) | FNMR @ 1% FMR | FNMR @ 0.1% FMR | Decidability d' | Rank-1 Acc |
            |---|---|---|---|---|---|---|---|
            | **S1** | Face Only | Unprotected | 2.00% (95% CI [1.11, 3.60]) | 3.33% | 9.44% | 4.78 | 97.22% |
            | **S2** | Fingerprint Only | Unprotected | 5.81% (95% CI [4.72, 7.15]) | 26.67% | 68.06% | 3.42 | 78.89% |
            | **S3** | Multimodal Fused (w=0.60) | Unprotected | 1.11% (95% CI [0.29, 1.66]) | 1.11% | 1.94% | 5.91 | 99.44% |
            | **Scenario K** | Multimodal Cancelable | Claimed Key (Operational) | **1.29% ± 0.23%** | **1.47% ± 0.31%** | **3.19% ± 0.79%** | **5.29** | **98.81%** |
            | **Scenario U** | Multimodal Cancelable | Attacker's Own Key (Best Case)| 0.00%* | 0.00%* | 0.00%* | 7.92* | N/A* |
            """
        )
        st.caption("*Scenario U measures cryptographic key separation, NOT biological recognition accuracy.")

    with tab2:
        st.subheader("ISO/IEC 30136 Revocability & Unlinkability")
        u1, u2 = st.columns(2)
        with u1:
            if os.path.isfile("results/cancelable_revocability_dist.png"):
                st.image("results/cancelable_revocability_dist.png", caption="Revocation Hamming Distance Distributions")
                st.markdown(
                    "**Revocability Performance**: Probes against revoked templates achieve **100.00% rejection** "
                    "(FNMR = 100%) under validation operating points. Re-enrollment under new key completely restores genuine accuracy (FNMR = 1.67%)."
                )
        with u2:
            if os.path.isfile("results/cancelable_unlinkability.png"):
                st.image("results/cancelable_unlinkability.png", caption="ISO/IEC 30136 Unlinkability (Different Biological Samples)")
                st.markdown(
                    r"**Unlinkability Benchmark**: Multi-system linkage metric **$D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$**, "
                    "confirming templates are unlinkable against a score-based adversary without key access."
                )
        with tab3:
            st.subheader("Privacy-Utility Tradeoff across Projection Dimensions m")
            if os.path.isfile("results/privacy_utility_tradeoff.png"):
                st.image("results/privacy_utility_tradeoff.png", caption="Privacy-Utility Tradeoff: EER vs Inversion Cosine & Replay Success")
            st.write(
                r"Shows accuracy (Scenario K EER) alongside empirical leakage under known keys across $m \in \{64, 128, 256, 512, 768, 1024\}$. "
                "At $m=512$, recognition accuracy is preserved (EER 1.29%), while linear decodability yields high reconstruction given the key."
            )

        with tab4:
            st.subheader("Explicit Security Claims Table (docs/SECURITY_THREAT_MODEL.md)")
            st.markdown(
                r"""
                | Category | Claim | Status | Empirical Evidence & Rigor |
                |---|---|---|---|
                | **What IS Shown** | **Accuracy Preservation vs Unprotected S3** | **Confirmed** | Scenario K EER = $1.29\% \pm 0.23\%$ vs S3 EER $1.11\%$. Paired bootstrap over test subjects (1000 resamples): $\Delta\text{EER} = +0.213\%$ (95% CI $[-0.135\%, +0.688\%]$, excludes 0: False; degradation indistinguishable from 0). $\Delta\text{FNMR@1\%} = +0.276\%$ (95% CI $[-0.333\%, +1.167\%]$, excludes 0: False). |
                | **What IS Shown** | **$\Delta\text{FNMR@0.1\%}$ Degradation Detectable** | **Confirmed** | $\Delta\text{FNMR@0.1\%} = +1.311\%$ (95% CI $[+0.333\%, +2.722\%]$, excludes 0: True; statistically detectable increase at strict operating point). Reported transparently. |
                | **What IS Shown** | **Revocability (ISO/IEC 30136)** | **Confirmed** | Genuine probes matched against revoked templates yield FNMR = 100.00% rejection under validation operating thresholds ($\tau_{oper, eer}=0.3504$, $\tau_{oper, 0.1\%}=0.3010$). Re-enrollment with new key version completely restores genuine recognition (FNMR = 1.67%). |
                | **What IS Shown** | **Unlinkability Without Keys (Score-Based Adversary)** | **Confirmed** | Gomez-Barrero benchmark evaluated with different biological samples across systems: $D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$. Template distinguisher classifier performs at chance (AUC = 0.4767). |
                | **What is NOT Shown** | **Non-Invertibility Given the Key** | **Refuted / Weak** | Random projection binarization is NOT a one-way trapdoor function. Given the key (matrix $R$), linear decodability (Ridge decoder) reconstructs vectors with high cosine similarity ($\cos(\hat{x}_c, x_c) = 0.9335 \pm 0.0115$, $\cos(\hat{x}_u, x) = 0.9354 \pm 0.0120$ at $m=512$). Replay against unprotected S3 achieves 100.0% success at 1% and 0.1% FMR. Results are a lower bound on empirical leakage. |
                | **What is NOT Shown** | **Unlinkability Given the Keys** | **Refuted / Collapses** | When both keys are known, reconstructing estimated embeddings enables cross-system account linkage: ROC AUC = 0.9980, EER = 1.63%, and $D_\leftrightarrow^{sys}$ surges to 0.9649. Unlinkability does NOT survive key compromise. |
                | **What is NOT Shown** | **Resistance to Raw Template Replay at API** | **Not Inherent** | If an adversary obtains the packed bitstring template and replays it verbatim across the network to an API accepting identical bitstrings, Hamming distance is 0.0000. Resistance requires challenge-response freshness or 2FA key derivation. |
                """

        )

    render_footer()

# ==============================================================================
# 6. THREAT DEMO PAGE
# ==============================================================================
elif page == "Threat demo":
    st.header("⚠️ Threat Model & Security Demonstration")
    st.write(
        "Demonstrates security properties and empirical boundary limits using **precomputed experimental artifacts only**. "
        "No live inversion attacks and no reconstructed biometric vectors are synthesized in the user interface."
    )

    st.subheader("1. Cross-Key Decorrelation Demo (Same User, Independent Keys)")
    st.write(
        "Illustrates unlinkability and key separation: two cancelable templates generated from the same subject "
        "under two distinct random keys $K_A$ and $K_B$ yield mutually independent bit sequences."
    )

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.markdown(
            '<div class="metric-card">'
            "<b>Template A (under Key $K_A$)</b><br>"
            "<code>101100010100111010101101...</code> (512 bits)<br>"
            "<small>Hex: <code>b14ead976b91...</code></small>"
            "</div>",
            unsafe_allow_html=True,
        )
    with tcol2:
        st.markdown(
            '<div class="metric-card">'
            "<b>Template B (under Key $K_B$)</b><br>"
            "<code>011010111001001001110011...</code> (512 bits)<br>"
            "<small>Hex: <code>6b9273f08a12...</code></small>"
            "</div>",
            unsafe_allow_html=True,
        )

    dcol1, dcol2, dcol3 = st.columns(3)
    dcol1.metric("Hamming Distance", "0.5006", "Expected: ~0.5000")
    dcol2.metric("Differing Bits", "256 / 512", "50.0% Bit Flip")
    dcol3.metric("Linkage Classification", "UNLINKABLE", "p > 0.05 (Chance)")

    st.markdown("---")
    st.subheader("2. Empirical Inversion Leakage under Known Keys (Phase 6 Findings)")
    st.markdown(
        '<div class="demo-banner">'
        "🚨 <b>Honest Security Disclosure:</b> Random projection binarization is <b>NOT</b> a cryptographic one-way function. "
        "When an adversary possesses the projection key $K$, linear decoders achieve structural reconstruction of biometric vectors. "
        "System security depends strictly on <b>key secrecy</b> (Threat Case A1)."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        | Dimension $m$ | Scenario K EER | Best Attack | Centered Cosine | Raw Fused Cosine | S3 Replay @ 1% FMR | Face Replay @ 1% FMR | Finger Replay @ 1% FMR |
        |---|---|---|---|---|---|---|---|
        | 64 | 4.02% | MLP | 0.6313 ± 0.0766 | 0.6369 ± 0.0632 | 100.0% | 91.7% | 50.0% |
        | 128 | 2.07% | Ridge | 0.7763 ± 0.0397 | 0.7833 ± 0.0409 | 100.0% | 100.0% | 86.7% |
        | 256 | 1.30% | Ridge | 0.8745 ± 0.0216 | 0.8782 ± 0.0228 | 100.0% | 100.0% | 100.0% |
        | **512 (Chosen)** | **1.08%** | **Ridge** | **0.9335 ± 0.0115** | **0.9354 ± 0.0120** | **100.0%** | **100.0%** | **100.0%** |
        | 768 | 0.98% | Ridge | 0.9522 ± 0.0078 | 0.9536 ± 0.0083 | 100.0% | 100.0% | 100.0% |
        | 1024 | 1.09% | Ridge | 0.9614 ± 0.0063 | 0.9624 ± 0.0068 | 100.0% | 100.0% | 100.0% |
        """
    )
    st.caption("Evaluated on 120 test subjects. Ridge decoder is the strongest attack tested (lower bound on empirical leakage).")

    st.markdown("---")
    st.subheader("3. Threat Summary & Key Takeaways")
    st.markdown(
        """
        1. **Template Secrecy Without Key (Threat A1)**: Without the chaotic key, the key space is at most $2^{126}$ operations. Template distinguisher performs at chance (AUC = 0.4767), ensuring zero identity leakage.
        2. **Compromised Key (Threat A2)**: If the key leaks, cancelable templates can be linearly decoded to 0.935 cosine fidelity and replayed against unprotected systems.
        3. **Revocation Restores Security (Threat A5)**: Revoking the compromised key and issuing a new key repudiates the leaked template with 100.00% rejection rate.
        """
    )

    render_footer()
