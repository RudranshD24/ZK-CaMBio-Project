"""scripts/build_results_manifest.py

Computes SHA-256 hashes and sizes of all files in results/ and writes results/MANIFEST.md.
"""

import hashlib
from pathlib import Path


def main() -> None:
    results_dir = Path("results")
    lines = [
        "# Results Artifacts Manifest\n\n",
        "Tracks the SHA-256 cryptographic checksum and byte size of every generated result artifact in `results/`.\n\n",
        "| File Name | Size (Bytes) | SHA-256 Checksum |\n",
        "|---|---|---|\n",
    ]
    for p in sorted(results_dir.iterdir()):
        if p.is_file() and p.name != "MANIFEST.md":
            data = p.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            lines.append(f"| `{p.name}` | {len(data):,} | `{sha}` |\n")

    manifest_path = results_dir / "MANIFEST.md"
    manifest_path.write_text("".join(lines), encoding="utf-8")
    print(f"Generated {manifest_path} with {len(lines) - 4} files.")

if __name__ == "__main__":
    main()
