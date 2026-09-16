"""Unit tests for DevA: Ingestion Pseudonymization (Invariant 6)."""

import pytest
from backend.common.schemas import IdentityType
from backend.ingestion.pseudonymizer import HMACIdentityPseudonymizer


def test_pseudonym_format_and_determinism():
    p = HMACIdentityPseudonymizer()
    raw_id = "alice.developer@corp.internal"

    token1 = p.pseudonymize(raw_id, identity_type=IdentityType.HUMAN)
    token2 = p.pseudonymize(raw_id, identity_type=IdentityType.HUMAN)

    assert token1 == token2
    assert token1.startswith("Subject-")
    parts = token1.split("-")
    assert len(parts) == 3
    assert parts[0] == "Subject"
    assert parts[1].isalpha()
    assert parts[2].isdigit() and len(parts[2]) == 3


def test_non_human_identity_tokens():
    p = HMACIdentityPseudonymizer()

    sa_token = p.pseudonymize("sa-deployer@gcp.iam", identity_type=IdentityType.SERVICE_ACCOUNT)
    assert sa_token.startswith("ServiceAccount-")

    runner_token = p.pseudonymize("github-runner-eu-01", identity_type=IdentityType.CICD_RUNNER)
    assert runner_token.startswith("Runner-")


def test_sealed_vault_and_unmasking():
    p = HMACIdentityPseudonymizer()
    raw_id = "bob.researcher@corp.internal"
    token = p.pseudonymize(raw_id)

    # Decrypt with correct master key
    revealed = p.unmask_with_key(token, p.vault_master_key)
    assert revealed == raw_id

    # Decrypt with incorrect key fails cleanly
    fake_key = b"0" * 32
    bad_reveal = p.unmask_with_key(token, fake_key)
    assert bad_reveal is None


def test_distinct_identities_yield_distinct_tokens():
    p = HMACIdentityPseudonymizer()
    tokens = {
        p.pseudonymize(f"user_{i}@corp.internal")
        for i in range(50)
    }
    # All 50 unique identities should have unique tokens
    assert len(tokens) == 50
