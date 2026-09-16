---
name: skill_execute_cusum_drift
description: Computes unanchored behavioral displacement against fast/slow baselines and updates the cumulative CUSUM drift score.
---

# `skill_execute_cusum_drift`

Computes unanchored behavioral displacement against fast/slow baselines and updates the cumulative CUSUM drift score.

## Formulas
- **Unanchored Displacement:**
  $$D_t = \delta_t \cdot \| \mathbf{z}_t - \mathbf{z}_{\text{baseline}} \|_2$$
  where $\delta_t \in [0.15, 1.0]$ is the context discount factor.
- **Recursive CUSUM Drift Accumulation:**
  $$S_0 = 0$$
  $$S_t = \max(0, S_{t-1} + D_t - \mu_{\text{cohort}} - k)$$
  where $k$ is the allowable slack parameter and $\mu_{\text{cohort}}$ is the peer drift rate.

## Outputs
- `drift_score`: $S_t$
- `drift_velocity`: $S_t - S_{t-1}$
- `trajectory_state`: `["STABLE", "CONTEXTUAL_DRIFT", "UNANCHORED_EXPLORATION", "HIGH_RISK_TRAJECTORY", "CRITICAL"]`
- `dimension_attribution`: Dimension-level z-score deviations for forensic explainability.

## Implementation Target
- Implementation: `backend/drift/cusum.py` and `backend/drift/baselines.py`
