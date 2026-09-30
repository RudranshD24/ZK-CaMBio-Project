"""src/face/encoder.py

Face feature encoder using InceptionResnetV1 pretrained on VGGFace2.
Extracts 512-dimensional L2-normalized facial embeddings.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from PIL import Image


class FaceEncoder:
    """Extracts 512-dimensional face embeddings from PIL images."""

    def __init__(
        self,
        pretrained: str | None = "vggface2",
        weights_path: str | Path | None = None,
        device: str | None = None,
    ) -> None:
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Check local weights to avoid runtime network download
        resolved_weights = None
        if weights_path is not None and Path(weights_path).is_file():
            resolved_weights = Path(weights_path)
        elif Path("models/vggface2.pt").is_file():
            resolved_weights = Path("models/vggface2.pt")

        if resolved_weights is not None:
            self.model = InceptionResnetV1(pretrained=None).eval().to(self.device)
            state_dict = torch.load(resolved_weights, map_location=self.device)
            self.model.load_state_dict(state_dict, strict=False)
        else:

            self.model = InceptionResnetV1(pretrained=pretrained).eval().to(self.device)

        self.embedding_dim = 512


    def preprocess(self, img: Image.Image) -> torch.Tensor:
        """Preprocesses a PIL image to a normalized (3, 160, 160) tensor."""
        if img.mode != "RGB":
            img = img.convert("RGB")
        if img.size != (160, 160):
            img = img.resize((160, 160), Image.Resampling.BILINEAR)

        # Standard face normalization: (x - 127.5) / 128.0
        arr = np.array(img, dtype=np.float32)
        tensor = torch.from_numpy(arr).permute(2, 0, 1)
        tensor = (tensor - 127.5) / 128.0
        return tensor

    def extract_embedding(self, img: Image.Image) -> np.ndarray:
        """Extracts and returns a single L2-normalized 512-d embedding."""
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.model(tensor).squeeze(0).cpu().numpy()
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb.astype(np.float32)

    def extract_batch(self, images: list[Image.Image]) -> np.ndarray:
        """Extracts and returns L2-normalized embeddings for a batch of images."""
        if not images:
            return np.empty((0, self.embedding_dim), dtype=np.float32)

        tensors = torch.stack([self.preprocess(img) for img in images]).to(self.device)
        with torch.no_grad():
            embs = self.model(tensors).cpu().numpy()

        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        embs = embs / norms
        return embs.astype(np.float32)
