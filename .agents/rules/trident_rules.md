# TRIDENT Architecture & Development Invariants

1. **Deterministic Risk Computation:** Never use raw LLMs to calculate risk numbers or alert severities. Composite risk calculation is strictly deterministic and mathematical.
2. **Context Discount Cap ($\delta \le 0.85$):** Context attenuates risk, never erases it. Minimum residual risk is strictly 15% ($\delta(e) \ge 0.15$).
3. **Protected Endpoint Filtering:** Ingestion must filter whistleblower, ethics hotline, and ombudsman endpoints *before* graph ingestion.
4. **HMAC-SHA-256 Pseudonymization:** Ingestion pseudonymizes human identifiers (`Subject-[ALPHA]-[0-9]{3}`) before graph creation. Identity reveal uses Shamir 2-of-3 threshold custody.
5. **No Future Data Leakage:** All synthetic test scenarios and baselines strictly adhere to chronological ordering.
6. **Claim Ledger Rigor:** Every metric carries a claim label (`Measured Today`, `External Reference`, `Target`, or `Removed`).
