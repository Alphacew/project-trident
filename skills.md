# Project TRIDENT — Antigravity Agent Skills & Tooling Specifications

This document catalogs the operational skills and automated procedures available to agents working within the TRIDENT repository.

---

## Skill 1: `skill_normalize_ocsf_event`
- **Description:** Parses incoming telemetry events into OCSF-compliant canonical records, enforces the Protected Endpoint Filter, and applies pseudonymization.
- **Execution Target:** `backend/ingestion/normalizer.py`
- **Inputs:**
  - `raw_event`: Raw JSON payload (Okta, CloudTrail, GitHub, Jira, ServiceNow, PagerDuty).
  - `protected_registry`: List of protected URIs, hotlines, emails, or CIDRs.
  - `salt_key`: Secret salt for HMAC-SHA-256 pseudonymization.
- **Outputs:**
  - Normalized event dict or `None` (if dropped via protected filter).
- **Procedural Rules:**
  1. Inspect `target_endpoint` and `destination_address`.
  2. If matched against `protected_registry`, route record to encrypted audit log and return `DROP_FROM_GRAPH`.
  3. Hash `actor.user_id` and `actor.email` using `HMAC-SHA-256(identifier, salt_key)`. Map to token format `Subject-[ALPHA]-[0-9]{3}`.
  4. Output normalized schema with standard fields: `event_id`, `timestamp`, `actor_token`, `action`, `resource`, `network_context`, `source_type`.

---

## Skill 2: `skill_compute_cas_signals`
- **Description:** Evaluates the ten signals of the Context Authenticity Score ($CAS$) against candidate organizational anchors (e.g., Jira tickets, ServiceNow changes).
- **Execution Target:** `backend/trust/authenticity.py`
- **Mathematical Specification:**
  $$CAS = \sigma \left( \sum_{i=1}^{10} w_i \cdot s_i \right) = \frac{1}{1 + e^{-\sum_{i=1}^{10} w_i \cdot s_i}}$$
  where $s_i \in [-1, 1]$ represents each normalized signal indicator and $w_i > 0$ represents the calibrated signal weight.
- **Signal Implementations:**
  1. `s1_temporal_mismatch`: Distance between ticket creation and event. Ticket created $< 5$ minutes before action returns negative score.
  2. `s2_approver_conflict`: Requester and approver share direct hierarchical reporting line or are identical.
  3. `s3_emergency_abuse`: Frequency of emergency/expedited tickets by actor over 30 days exceeds cohort mean by $> 2.5\sigma$.
  4. `s4_sod_violation`: Separation-of-duties conflict (e.g., actor approved own access request).
  5. `s5_stale_hr_metadata`: Access requested for previous team or deprecated project tag.
  6. `s6_scope_mismatch`: Semantic divergence (cosine distance) between ticket description and accessed target resource/table.
  7. `s7_cross_signal_inconsistency`: Absence of correlated Slack/Teams discussions, PR reviews, or calendar meetings during the event window.
  8. `s8_ticket_velocity_anomaly`: Spurt of tickets created within a short window.
  9. `s9_ghost_ticket`: Zero downstream commits, pull requests, deploy events, or status transitions following ticket resolution.
  10. `s10_post_hoc_modification`: Ticket updated, retrofitted, or re-scoped after anomalous behavior occurred.

---

## Skill 3: `skill_calculate_anchor_discount`
- **Description:** Calculates the organizational anchor score and caps the contextual attenuation factor.
- **Execution Target:** `backend/trust/anchor_engine.py`
- **Formulas:**
  $$\text{AnchorScore}(e) = \max_{a \in A} \left( \text{Auth}(a) \cdot CAS(a) \cdot \text{ScopeMatch}(a, e) \cdot e^{-\lambda (t_e - t_a)} \right)$$
  $$\delta(e) = 1 - \min(0.85, \kappa \cdot \text{AnchorScore}(e))$$
- **Invariants:**
  - $\delta(e) \ge 0.15$ at all times. No context may reduce residual risk below $15\%$.
- **Outputs:**
  - `anchor_score` $\in [0, 1]$
  - `discount_factor` $\delta \in [0.15, 1.0]$
  - `selected_anchor_id`

---

## Skill 4: `skill_execute_cusum_drift`
- **Description:** Computes unanchored behavioral displacement against fast/slow baselines and updates the cumulative CUSUM drift score.
- **Execution Target:** `backend/drift/cusum.py`
- **Formulas:**
  - Unanchored Displacement:
    $$D_t = \delta_t \cdot \| \mathbf{z}_t - \mathbf{z}_{\text{baseline}} \|_2$$
  - Recursive CUSUM Drift Accumulation:
    $$S_0 = 0$$
    $$S_t = \max(0, S_{t-1} + D_t - \mu_{\text{cohort}} - k)$$
    where $k$ is the allowable slack parameter and $\mu_{\text{cohort}}$ is the peer drift rate.
- **Outputs:**
  - `drift_score`: $S_t$
  - `drift_velocity`: $S_t - S_{t-1}$
  - `trajectory_state`: `["STABLE", "CONTEXTUAL_DRIFT", "UNANCHORED_EXPLORATION", "HIGH_RISK_TRAJECTORY", "CRITICAL"]`

---

## Skill 5: `skill_shamir_custody`
- **Description:** Manages Shamir 2-of-3 secret sharing for pseudonymous identity encryption and threshold unmasking ceremonies.
- **Execution Target:** `backend/crypto/shamir_vault.py`
- **Operations:**
  - `split_identity(real_id: str) -> Tuple[ShareA, ShareB, ShareC]`:
    - Generates 256-bit AES key.
    - Encrypts `real_id` with AES-GCM.
    - Splits key into 3 polynomial shares over $GF(2^8)$ or standard prime field ($k=2, n=3$):
      - Share A: SOC Lead
      - Share B: Data Protection Officer / Legal
      - Share C: Works Council / HR Representative
  - `reconstruct_identity(shares: List[Share], justification: str, auditor_token: str) -> str`:
    - Validates presence of at least 2 distinct authorized shares.
    - Interpolates polynomial to recover key.
    - Decrypts and returns `real_id`.
    - Immutably writes event to `audit_vault_reveal_log`.

---

## Skill 6: `skill_extract_causal_subgraph`
- **Description:** Prunes the global temporal enterprise graph down to a minimal causal evidence subgraph for SOC analyst consumption.
- **Execution Target:** `backend/graph/subgraph_extractor.py`
- **Inputs:**
  - `seed_actor_token`: Subject pseudonym.
  - `time_window`: $(t_{\text{start}}, t_{\text{end}})$.
  - `min_edge_risk`: Threshold to include traversal edges.
- **Outputs:**
  - Serialized graph payload formatted for React Flow with node classifications:
    - Root credential event
    - Privilege escalation edge
    - Discovery edge
    - Target resource access
    - Staging/Outbound connection
    - Simulated canary trip node

---

## Skill 7: `skill_run_synthetic_scenario`
- **Description:** Generates, loads, and executes the five canonical test scenarios to validate engine differentiation.
- **Execution Target:** `tests/scenarios/scenario_runner.py`
- **Test Matrix:**
  1. **Scenario A (Legitimate Role Change):** Promoted developer accesses new repo and DB. High Jira/HR anchor $\implies$ $CAS \approx 0.95 \implies$ Risk attenuated.
  2. **Scenario B (Low-and-Slow Insider):** Five sensitive files queried daily over 14 days without ticket anchor $\implies$ Individual anomalies low, but CUSUM $S_t$ steadily climbs past Tier 3 threshold.
  3. **Scenario C (Fabricated Context):** Suspicious DB access preceded 4 minutes by self-approved Jira ticket. $CAS \le 0.25 \implies$ Discount capped $\implies$ Alert triggers.
  4. **Scenario D (Emergency Incident):** Off-hours root query justified by open PagerDuty critical incident $\implies$ Authenticity high $\implies$ Suppressed.
  5. **Scenario E (Compromised Service Account):** CI/CD runner queries uncharacteristic metadata endpoint $\implies$ NHI risk spikes without human role anchor.
- **Verification Rule:**
  - The test suite fails if Scenario C is attenuated by more than $20\%$, or if Scenario A raises a Tier 3 alert.

---

## Skill 8: `skill_audit_managerial_protection`
- **Description:** Analyzes SOC query logs to prevent the platform from being weaponized by biased managers against specific subordinates.
- **Execution Target:** `backend/crypto/harassment_audit.py`
- **Audit Rules:**
  1. **Direct Name Query Block:** Block queries specifying named individuals. All investigations must originate from graph anomaly IDs or risk clusters.
  2. **Repeat Subject Alert:** If a pseudonym is subjected to $> 3$ manual SOC reviews within a 14-day window without progressing to Tier 3 or Tier 4, trigger an automatic compliance flag for the DPO.
  3. **Manager View Redaction:** Ensure all manager-tier dashboard views aggregate strictly at the peer cohort or team level ($N \ge 5$), stripping individual identifiers and subject tokens.