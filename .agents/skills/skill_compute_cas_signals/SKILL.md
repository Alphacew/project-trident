---
name: skill_compute_cas_signals
description: Evaluates the ten signals of the Context Authenticity Score (CAS) against candidate organizational anchors.
---

# `skill_compute_cas_signals`

Evaluates the ten signals of the Context Authenticity Score ($CAS$) against candidate organizational anchors (Jira tickets, ServiceNow changes, PagerDuty incidents).

## Mathematical Specification
$$CAS = \sigma \left( \sum_{i=1}^{10} w_i \cdot s_i \right) = \frac{1}{1 + e^{-\sum_{i=1}^{10} w_i \cdot s_i}}$$
where $s_i \in [-1, 1]$ represents each normalized signal indicator and $w_i > 0$ represents the calibrated signal weight.

## Signal Implementations
1. `s1_temporal_mismatch`: Distance between ticket creation and event. Ticket created $< 5$ minutes before action returns negative score.
2. `s2_approver_conflict`: Requester and approver share direct hierarchical reporting line or are identical.
3. `s3_emergency_abuse`: Frequency of emergency/expedited tickets by actor over 30 days exceeds cohort mean by $> 2.5\sigma$.
4. `s4_sod_violation`: Separation-of-duties conflict (e.g., actor approved own access request).
5. `s5_stale_hr_metadata`: Access requested for previous team or deprecated project tag.
6. `s6_scope_mismatch`: Semantic divergence between ticket description and accessed target resource/table.
7. `s7_cross_signal_inconsistency`: Absence of correlated Slack/Teams discussions, PR reviews, or calendar meetings during event window.
8. `s8_ticket_velocity_anomaly`: Spurt of tickets created within a short window.
9. `s9_ghost_ticket`: Zero downstream commits, pull requests, deploy events, or status transitions following ticket resolution.
10. `s10_post_hoc_modification`: Ticket updated, retrofitted, or re-scoped after anomalous behavior occurred.

## Implementation Target
- Implementation: `backend/trust/authenticity.py` and `backend/trust/signals.py`
