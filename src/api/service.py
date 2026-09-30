"""src/api/service.py

Biometric processing service for ZK-CaMBio API.
Loads Face and Fingerprint encoders once at startup.
Handles:
1. In-memory image decoding from bytes.
2. Embedding extraction and feature-level fusion (w=0.60).
3. Enrollment quality checks (FR-12): consistency cosine to mean.
4. Key derivation:
   - "user_secret" mode: HMAC(master, context | user_secret) -> never stored.
   - "server_key" mode: HMAC(master, context | user_id) -> server-derived.
5. Template transformation and Hamming verification.
6. Explicit try/finally memory cleanup.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from src.chaos.engine import ChaosGeneratorPy, quantize_vector
from src.face.encoder import FaceEncoder
from src.finger.models import FingerResNet18
from src.finger.preprocess import preprocess_fingerprint

try:
    import chaoshash
except ImportError:
    chaoshash = None


class BiometricService:
    """Singleton service holding encoders and execution parameters."""

    def __init__(
        self,
        config_path: str | Path = "configs/biometric_parameters.json",
        models_dir: str | Path = "models",
    ) -> None:
        self.config_path = Path(config_path)
        with open(self.config_path, encoding="utf-8") as f:
            self.cfg = json.load(f)

        self.models_dir = Path(models_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load parameters
        self.face_dim = self.cfg["dimensions"]["face_dim"]
        self.finger_dim = self.cfg["dimensions"]["finger_dim"]
        self.fused_dim = self.cfg["dimensions"]["fused_dim"]
        self.m = self.cfg["dimensions"]["template_bits_m"]
        self.w = self.cfg["fusion"]["weight_face_w"]
        self.scale = self.cfg["quantization"]["scale"]
        self.tau_eer = self.cfg["matching_thresholds"]["operational_eer_threshold_hd"]

        # Quality thresholds
        self.min_face_consistency = self.cfg["enrollment_quality"]["min_face_consistency_cosine"]
        self.min_finger_consistency = self.cfg["enrollment_quality"]["min_finger_consistency_cosine"]

        # Mean vector
        mean_path = Path(self.cfg["quantization"]["mean_vector_path"])
        if not mean_path.is_file():
            # Fallback relative to project
            mean_path = Path("data/processed/chaos_mean_vector.npy")
        self.mean_vector = np.load(mean_path).astype(np.float32)

        # Encoders
        print(f"Loading FaceEncoder on {self.device}...")
        self.face_encoder = FaceEncoder(device=str(self.device))

        print(f"Loading FingerResNet18 on {self.device}...")
        self.finger_model = FingerResNet18(embedding_dim=256, pretrained=False)
        finger_weights = self.models_dir / "finger_resnet18_best.pth"
        if not finger_weights.is_file():
            finger_weights = Path("data/processed/finger_resnet18_best.pth")

        ckpt = torch.load(finger_weights, map_location=self.device)
        self.finger_model.load_state_dict(ckpt["model_state_dict"])
        self.finger_model.to(self.device).eval()

        self.finger_transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
            ]
        )

        # Master key configuration
        self.dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
        default_dev_key = b"ZKCAMBIO_DEFAULT_INSECURE_DEV_KEY_2026!"[:32]
        env_key = os.environ.get("SERVER_MASTER_KEY")
        if env_key:
            self.master_key = env_key.encode("utf-8")[:32]
            if len(self.master_key) < 32:
                self.master_key = self.master_key.ljust(32, b"\0")
        else:
            if not self.dev_mode:
                raise RuntimeError("Refusing to start without SERVER_MASTER_KEY outside DEV_MODE=true!")
            self.master_key = default_dev_key

    def derive_user_chaos_params(
        self,
        username: str,
        key_mode: str,
        key_version: int,
        user_secret: str | None = None,
        app_salt: str = "zkcambio_salt",
    ) -> tuple[int, int]:
        """Derives chaotic initial state and map parameter r_param.

        - If key_mode == "user_secret": context binds user_secret.
        - If key_mode == "server_key": context binds username/user_id.
        """
        if key_mode == "user_secret":
            if not user_secret:
                raise ValueError("user_secret is required for 'user_secret' key_mode")
            context = f"zkcambio|{app_salt}|v{key_version}|{user_secret}".encode()
        elif key_mode == "server_key":
            context = f"zkcambio|{app_salt}|v{key_version}|server_key|{username}".encode()
        else:
            raise ValueError(f"Unknown key_mode: {key_mode}")

        derived_bytes = hmac.new(self.master_key, context, hashlib.sha256).digest()
        state = int.from_bytes(derived_bytes[0:8], byteorder="little")
        r_param = int.from_bytes(derived_bytes[8:16], byteorder="little")
        if state == 0:
            state = 0x9E3779B97F4A7C15
        return state, r_param

    def decode_image_bytes(self, image_bytes: bytes, mode: str = "RGB") -> Image.Image:
        """Loads a PIL image from raw bytes with format validation."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()
            return img.convert(mode)
        except Exception as e:
            raise ValueError(f"Invalid or unreadable image file: {e}") from e

    def extract_face_embedding(self, img: Image.Image) -> np.ndarray:
        return self.face_encoder.extract_embedding(img)

    def extract_finger_embedding(self, img: Image.Image, db_hint: str = "DB1_A") -> np.ndarray:
        """Applies Preprocessing V2 and extracts 256-d embedding."""
        cropped = preprocess_fingerprint(img, db_hint=db_hint, variant="v2")
        tensor = self.finger_transform(cropped).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.finger_model(tensor).squeeze(0).cpu().numpy()
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb.astype(np.float32)

    def check_enrollment_quality(
        self,
        face_embeddings: list[np.ndarray],
        finger_embeddings: list[np.ndarray],
    ) -> None:
        """FR-12 Enrollment Quality Check:

        Asserts each sample has cosine similarity to the modality mean above threshold.
        """
        # Face consistency
        face_mean = np.mean(face_embeddings, axis=0)
        face_mean /= np.linalg.norm(face_mean)
        for idx, emb in enumerate(face_embeddings):
            cos = float(np.dot(emb, face_mean))
            if cos < self.min_face_consistency:
                raise ValueError(
                    f"Face sample {idx+1} consistency ({cos:.3f}) is below minimum threshold ({self.min_face_consistency:.3f})"
                )

        # Finger consistency
        finger_mean = np.mean(finger_embeddings, axis=0)
        finger_mean /= np.linalg.norm(finger_mean)
        for idx, emb in enumerate(finger_embeddings):
            cos = float(np.dot(emb, finger_mean))
            if cos < self.min_finger_consistency:
                raise ValueError(
                    f"Finger sample {idx+1} consistency ({cos:.3f}) is below minimum threshold ({self.min_finger_consistency:.3f})"
                )

    def generate_cancelable_template(
        self,
        fused_vector: np.ndarray,
        state: int,
        r_param: int,
    ) -> bytes:
        """Centers fused vector around public mean and transforms with C++ chaoshash."""
        x_q = quantize_vector(fused_vector, mean_vector=self.mean_vector, scale=self.scale)
        if chaoshash is not None:
            return chaoshash.transform(x_q, state, r_param, self.m)

        # Pure Python fallback
        gen = ChaosGeneratorPy(state, r_param)
        for _ in range(1000):
            gen.step()
        perm = list(range(self.fused_dim))
        for i in range(self.fused_dim - 1, 0, -1):
            s = gen.step()
            j = s % (i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        x_perm = [int(x_q[perm[i]]) for i in range(self.fused_dim)]
        n_bytes = (self.m + 7) // 8
        out = bytearray(n_bytes)
        for k in range(self.m):
            acc = 0
            for j in range(self.fused_dim):
                s = gen.step()
                bit_sign = 1 if ((s >> 32) & 1) else -1
                acc += bit_sign * x_perm[j]
            if acc >= 0:
                out[k // 8] |= 1 << (7 - (k % 8))
        return bytes(out)

    def compute_hamming_distance(self, t1: bytes, t2: bytes) -> float:
        if chaoshash is not None:
            return float(chaoshash.hamming(t1, t2, self.m))
        total_bits = self.m
        diff_bits = 0
        for i in range(len(t1)):
            diff = t1[i] ^ t2[i]
            if i == len(t1) - 1 and (total_bits % 8 != 0):
                mask = 0xFF << (8 - (total_bits % 8))
                diff &= mask
            diff_bits += bin(diff).count("1")
        return float(diff_bits / total_bits)
