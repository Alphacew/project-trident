"""HMAC-SHA-256 Ingestion Pseudonymization for Project TRIDENT.

Enforces Invariant 6:
Human and non-human identifiers are hashed and replaced with pseudonyms
(e.g., Subject-Theta-482) via HMAC-SHA-256 immediately at ingestion before
any graph construction or behavioral aggregation.

Includes:
- Keyed HMAC-SHA-256 mapping
- Standard phonetic code token generator (Subject-Theta-482)
- AES-256-GCM sealed reverse vault mapping (protected under dual-custody architecture)
"""

from __future__ import annotations

import hmac
import hashlib
import os
import secrets
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.common.schemas import IdentityType

# Phonetic alphabet list for consistent, human-readable subject tokens
PHONETIC_ALPHABET = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel",
    "India", "Juliett", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa",
    "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey",
    "Xray", "Yankee", "Zulu", "Theta", "Omega", "Sigma", "Lambda", "Kappa"
]


class HMACIdentityPseudonymizer:
    """Ingestion-time pseudonymizer converting raw employee/system IDs into pseudonyms."""

    def __init__(
        self,
        hmac_salt: Optional[bytes] = None,
        vault_master_key: Optional[bytes] = None
    ) -> None:
        # Secret salt used for HMAC-SHA-256 hashing
        self._hmac_salt = hmac_salt or secrets.token_bytes(32)
        # AES-256 key for sealing the reverse lookup table
        self._vault_master_key = vault_master_key or AESGCM.generate_key(bit_length=256)
        self._aesgcm = AESGCM(self._vault_master_key)
        
        # Sealed reverse lookup store: token -> (nonce, ciphertext)
        self._sealed_vault: Dict[str, Tuple[bytes, bytes]] = {}
        # Forward cache for current session consistency
        self._token_cache: Dict[str, str] = {}

    @property
    def vault_master_key(self) -> bytes:
        """Returns the master key for threshold secret sharing integration."""
        return self._vault_master_key

    def pseudonymize(
        self,
        raw_identity: str,
        identity_type: IdentityType = IdentityType.HUMAN
    ) -> str:
        """Generates a deterministic pseudonymous token and seals the raw identity."""
        if not raw_identity:
            return "Subject-Unknown-000"

        norm_id = raw_identity.strip().lower()
        cache_key = f"{identity_type.value}:{norm_id}"
        
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]

        # Compute keyed HMAC-SHA-256
        h = hmac.new(self._hmac_salt, norm_id.encode("utf-8"), hashlib.sha256).digest()

        # Deterministically select phonetic prefix and 3-digit number
        phonetic_idx = int.from_bytes(h[:2], "big") % len(PHONETIC_ALPHABET)
        phonetic_code = PHONETIC_ALPHABET[phonetic_idx]
        num_code = int.from_bytes(h[2:4], "big") % 1000

        prefix = "Subject"
        if identity_type == IdentityType.SERVICE_ACCOUNT:
            prefix = "ServiceAccount"
        elif identity_type == IdentityType.CICD_RUNNER:
            prefix = "Runner"
        elif identity_type == IdentityType.API_KEY:
            prefix = "APIKey"

        token = f"{prefix}-{phonetic_code}-{num_code:03d}"

        # Seal the raw identity into the encrypted vault store
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, raw_identity.encode("utf-8"), token.encode("utf-8"))
        self._sealed_vault[token] = (nonce, ciphertext)
        self._token_cache[cache_key] = token

        return token

    def unmask_with_key(self, token: str, key: bytes) -> Optional[str]:
        """Decrypts a sealed pseudonym token given the authorized 256-bit vault key."""
        if token not in self._sealed_vault:
            return None
        nonce, ciphertext = self._sealed_vault[token]
        try:
            cipher = AESGCM(key)
            decrypted = cipher.decrypt(nonce, ciphertext, token.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def get_token_count(self) -> int:
        return len(self._sealed_vault)
