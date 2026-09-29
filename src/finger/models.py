"""src/finger/models.py

Baseline B: ResNet18 fine-tuned with CosFace margin loss for fingerprint feature extraction.
Produces 256-dimensional L2-normalized embeddings.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812
from torchvision.models import ResNet18_Weights, resnet18


class FingerResNet18(nn.Module):
    """ResNet18 adapted for single-channel grayscale 128x128 fingerprints,

    producing 256-dimensional L2-normalized embeddings.
    """

    def __init__(self, embedding_dim: int = 256, pretrained: bool = True) -> None:
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        base = resnet18(weights=weights)

        # Modify conv1 for 1-channel grayscale input (average RGB weights)
        orig_conv1 = base.conv1
        self.conv1 = nn.Conv2d(
            1,
            orig_conv1.out_channels,
            kernel_size=orig_conv1.kernel_size,
            stride=orig_conv1.stride,
            padding=orig_conv1.padding,
            bias=False,
        )
        if pretrained and weights is not None:
            with torch.no_grad():
                self.conv1.weight.copy_(orig_conv1.weight.mean(dim=1, keepdim=True))

        self.bn1 = base.bn1
        self.relu = base.relu
        self.maxpool = base.maxpool
        self.layer1 = base.layer1
        self.layer2 = base.layer2
        self.layer3 = base.layer3
        self.layer4 = base.layer4
        self.avgpool = base.avgpool

        # 512 -> 256 embedding head
        self.fc = nn.Linear(base.fc.in_features, embedding_dim)
        self.bn_head = nn.BatchNorm1d(embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Input: (B, 1, 128, 128)
        Output: (B, 256) L2-normalized embedding
        """
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)

        emb = self.fc(x)
        emb = self.bn_head(emb)
        norm = torch.norm(emb, p=2, dim=1, keepdim=True).clamp(min=1e-12)
        return emb / norm


class CosFaceMarginProduct(nn.Module):
    """Large Margin Cosine Loss (CosFace) head.

    Wang et al., "CosFace: Large Margin Cosine Loss for Deep Face Recognition", CVPR 2018.
    Scale s = 30.0, margin m = 0.35.
    """

    def __init__(self, in_features: int = 256, out_features: int = 150, s: float = 30.0, m: float = 0.35) -> None:
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        # Normalize weights
        norm_w = F.normalize(self.weight, p=2, dim=1)
        # Cosine similarity: (B, out_features)
        cosine = F.linear(embeddings, norm_w)

        # Apply margin to the target class
        one_hot = torch.zeros_like(cosine)
        one_hot.scatter_(1, labels.view(-1, 1).long(), 1.0)

        # Output = s * (cos(theta) - m * one_hot)
        output = self.s * (cosine - one_hot * self.m)
        return output
