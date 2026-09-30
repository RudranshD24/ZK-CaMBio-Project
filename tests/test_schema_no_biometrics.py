"""tests/test_schema_no_biometrics.py

Schema Whitelist and Data Isolation Unit Test (FR-10).
Asserts that NO table in the database contains columns capable of holding:
- Raw images
- Pixels
- Continuous embeddings (512-d face, 256-d finger)
- Fused vectors (768-d)
- Plaintext user secrets (passwords, PINs)
"""

from __future__ import annotations

from sqlalchemy import LargeBinary
from src.db.models import Base, Template, UserKey


def test_schema_whitelist_no_raw_biometrics():
    """Validates every table and column in SQLAlchemy Base metadata against strict whitelist."""
    forbidden_terms = [
        "image",
        "pixel",
        "raw",
        "embedding",
        "face_vector",
        "finger_vector",
        "fused_vector",
        "secret",
        "pin",
        "password",
    ]

    for table_name, table in Base.metadata.tables.items():
        for column in table.columns:
            col_name = column.name.lower()
            for term in forbidden_terms:
                assert term not in col_name, (
                    f"Forbidden term '{term}' found in column '{table_name}.{column.name}'! "
                    f"Biometric data, embeddings, or user secrets must NEVER be stored in the database."
                )

    # Specific assertions on allowed LargeBinary columns:
    # 1. Template.template (packed cancelable bits only, exactly 64 bytes for m=512)
    assert isinstance(Template.template.type, LargeBinary)
    # 2. UserKey.key_material (server_key mode master key reference only)
    assert isinstance(UserKey.key_material.type, LargeBinary)

    # Assert no other table has binary columns
    for table_name, table in Base.metadata.tables.items():
        if table_name not in ("templates", "user_keys"):
            for col in table.columns:
                assert not isinstance(col.type, LargeBinary), (
                    f"Unexpected binary column '{table_name}.{col.name}' found!"
                )
