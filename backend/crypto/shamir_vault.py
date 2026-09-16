"""Project TRIDENT — Shamir 2-of-3 Threshold Vault.

Implements Shamir's Secret Sharing (k=2, n=3 threshold) over a finite prime field:
- Share A: SOC Lead
- Share B: Data Protection Officer / Legal
- Share C: Works Council / HR Representative

Any 2 distinct shares can reconstruct the 256-bit vault key to unmask a pseudonym.
Every reveal ceremony logs an immutable audit receipt.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
import secrets
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# Standard prime larger than 2^256: 2^256 + 297
PRIME_256 = (1 << 256) + 297


class ShamirShare(BaseModel):
    """An individual threshold share held by an authorized custodian."""
    custodian_role: str  # "SOC_LEAD", "DPO_LEGAL", "WORKS_COUNCIL"
    custodian_name: str
    index: int  # 1, 2, or 3
    value_hex: str  # Hex-encoded y-coordinate


class RevealReceipt(BaseModel):
    """Immutable audit log entry of an identity reveal ceremony."""
    receipt_id: str
    timestamp: datetime
    subject_token: str
    unmasked_identity: str
    participating_custodians: List[str]
    justification: str
    auditor_token: str
    claim_label: str = Field(default="Measured Today")


class ShamirVault:
    """Manages Shamir 2-of-3 threshold keys and reveal ceremonies."""

    CUSTODIAN_ROLES = [
        ("SOC_LEAD", "Chief SOC Analyst", 1),
        ("DPO_LEGAL", "Data Protection Officer", 2),
        ("WORKS_COUNCIL", "Works Council Representative", 3),
    ]

    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or os.urandom(32)
        self.shares: Dict[int, ShamirShare] = {}
        self.reveal_log: List[RevealReceipt] = []
        self._split_master_key()

    def _split_master_key(self):
        """Splits the 256-bit master key into 3 polynomial shares (degree 1 for k=2)."""
        secret_int = int.from_bytes(self.master_key, "big")
        # Random slope a1 for f(x) = secret + a1 * x
        a1 = secrets.randbelow(PRIME_256 - 1) + 1

        for role, name, x in self.CUSTODIAN_ROLES:
            y = (secret_int + a1 * x) % PRIME_256
            val_hex = f"{y:064x}"
            self.shares[x] = ShamirShare(
                custodian_role=role,
                custodian_name=name,
                index=x,
                value_hex=val_hex,
            )

    def get_shares(self) -> List[ShamirShare]:
        """Returns the current 3 custodian shares."""
        return list(self.shares.values())

    def reconstruct_key(self, share_list: List[ShamirShare]) -> bytes:
        """Recovers the 256-bit key from any 2 distinct shares via Lagrange interpolation."""
        if len(share_list) < 2:
            raise ValueError("Threshold requires at least 2 distinct shares.")

        # Ensure distinct indices
        seen_indices = set()
        distinct_shares = []
        for s in share_list:
            if s.index not in seen_indices:
                seen_indices.add(s.index)
                distinct_shares.append(s)

        if len(distinct_shares) < 2:
            raise ValueError("Duplicate shares provided; at least 2 distinct shares required.")

        s1, s2 = distinct_shares[0], distinct_shares[1]
        x1, y1 = s1.index, int(s1.value_hex, 16)
        x2, y2 = s2.index, int(s2.value_hex, 16)

        # Lagrange interpolation at x = 0:
        # secret = y1 * (-x2) / (x1 - x2) + y2 * (-x1) / (x2 - x1) mod P
        inv1 = pow(x1 - x2, -1, PRIME_256)
        inv2 = pow(x2 - x1, -1, PRIME_256)

        term1 = (y1 * (-x2) * inv1) % PRIME_256
        term2 = (y2 * (-x1) * inv2) % PRIME_256

        secret_int = (term1 + term2) % PRIME_256
        return secret_int.to_bytes(32, "big")
