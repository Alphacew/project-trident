# TRIDENT — Trust-Anchored Risk Intelligence, Drift & Evidence Network

> **"Behavior is not suspicious merely because it is unusual. It becomes dangerous when its legitimate explanation is weak, its unexplained deviation accumulates, and the resulting trajectory crosses an actionable risk boundary."**

---

## Phase 1: Ingestion Pipeline, Cryptographic Identity & Trust Engine

Phase 1 establishes the foundational data contracts, privacy boundary, and trust evaluation mechanisms for Project TRIDENT, developed in parallel workstreams:

- **DevA (Ingestion & Privacy Boundary):**
  - Canonical `CanonicalEvent` OCSF-aligned Pydantic models mapping identity logs (Okta/Entra ID), cloud telemetry (AWS CloudTrail), and business context (Jira/ServiceNow/PagerDuty).
  - Protected-Endpoint Filter at the ingestion boundary to drop whistleblower, ombudsman, and legal disclosure endpoints before graph persistence.
  - HMAC-SHA-256 pseudonymization converting raw employee IDs into tokens (e.g. `Subject-Theta-482`) immediately at ingestion with an AES-256-GCM sealed reverse vault.

- **DevB (Context Authenticity Engine):**
  - 10-signal Context Authenticity Score ($CAS$) module evaluating temporal mismatch, approver conflict, emergency change abuse, separation-of-duties violations, stale HR metadata, scope mismatch, cross-signal inconsistency, ticket velocity anomaly, ghost tickets, and post-hoc edits.
  - Organizational Anchor Score calculation combining authority weight, $CAS$, semantic scope match, and exponential temporal decay.
  - Context discount factor enforcement strictly capping attenuation at $0.85$ (minimum $15\%$ residual risk baseline: $\delta \ge 0.15$).

---

## Architecture & Module Directory

```
project-trident/
├── backend/
│   ├── common/
│   │   ├── __init__.py
│   │   └── schemas.py              # Shared CanonicalEvent, AnchorCandidate & CAS models
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── protected_filter.py     # Skill 1: Protected-endpoint filtering & dual-auth registry
│   │   ├── pseudonymizer.py        # Skill 1: HMAC-SHA-256 pseudonymizer & sealed AES-GCM vault
│   │   └── normalizer.py           # Skill 1: OCSF event normalizer for Okta, CloudTrail, Jira
│   └── trust/
│       ├── __init__.py
│       ├── authenticity.py         # Skill 2: 10-signal Context Authenticity Score (CAS)
│       └── anchor_engine.py        # Skill 3: Anchor evaluation & discount cap (δ ≥ 0.15)
├── tests/
│   ├── test_protected_filter.py    # Invariant 1 tests: 100% drop of whistleblower/ethics endpoints
│   ├── test_pseudonymizer.py       # Invariant 6 tests: phonetic tokens & cryptographic sealing
│   ├── test_normalizer.py          # Skill 1 tests: multi-source OCSF canonicalization
│   ├── test_cas_signals.py         # Skill 2 tests: 10 individual CAS signal evaluations
│   ├── test_anchor_engine.py       # Skill 3 tests: anchor scoring & Invariant 4 discount cap
│   └── test_phase1_integration.py  # End-to-end pipeline test from raw telemetry to discounted risk
├── pytest.ini
├── requirements.txt
├── test.sh
└── README.md
```

---

## Non-Negotiable Invariants

1. **Protected-Endpoint Filtering at Ingestion:**
   Edges touching protected endpoints (ethics hotlines, ombudsman portals, whistleblower channels, designated journalistic/legal contacts) are dropped *before* ingestion into the behavioral graph.
2. **Strict Separation of Protected-Class Data:**
   Protected-class labels and sensitive HR metadata reside in a sealed store for DPO auditing only and never enter graph representations.
3. **Context Authenticity Precedes Attenuation:**
   The 10-signal Context Authenticity Score ($CAS$) is computed *before* calculating the context discount factor ($\delta$).
4. **Context Discount Cap ($\delta \le 0.85$):**
   Context attenuates risk, but never erases it. $\delta \ge 0.15$ at all times (minimum $15\%$ residual risk baseline).
5. **Ingestion-Time Pseudonymization:**
   Human and non-human identifiers are hashed and replaced with pseudonyms (e.g. `Subject-Theta-482`) via HMAC-SHA-256 before any graph construction.
6. **Deterministic Mathematics:**
   Zero raw LLMs in risk calculation, CAS signal evaluation, or discount factors.

---

## Running the Verification Suite

```bash
# Run all unit and integration tests with coverage
./test.sh
```
