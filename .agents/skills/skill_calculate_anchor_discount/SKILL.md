---
name: skill_calculate_anchor_discount
description: Calculates the organizational anchor score and caps the contextual attenuation factor at 0.85 (minimum 15% residual risk).
---

# `skill_calculate_anchor_discount`

Calculates the organizational anchor score and caps the contextual attenuation factor.

## Formulas
$$\text{AnchorScore}(e) = \max_{a \in A} \left( \text{Auth}(a) \cdot CAS(a) \cdot \text{ScopeMatch}(a, e) \cdot e^{-\lambda (t_e - t_a)} \right)$$
$$\delta(e) = 1 - \min(0.85, \kappa \cdot \text{AnchorScore}(e))$$

## Invariants
- $\delta(e) \ge 0.15$ at all times. No context may reduce residual risk below $15\%$.
- Context attenuates risk, never erases it.

## Outputs
- `anchor_score` $\in [0, 1]$
- `discount_factor` $\delta \in [0.15, 1.0]$
- `selected_anchor_id`

## Implementation Target
- Implementation: `backend/trust/anchor_engine.py`
