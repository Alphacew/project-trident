# Project TRIDENT — Compiler & Assistant Directives

You are developing TRIDENT (Trust-Anchored Risk Intelligence, Drift & Evidence Network).

## Key Principles
1. Never propose using raw LLMs to calculate risk numbers or alert severities. Risk computation is strictly deterministic and mathematical.
2. Context discounts are capped at 0.85 ($\delta \le 0.85$). Context attenuates, never erases.
3. Protected endpoints (ethics, whistleblower, ombudsman) MUST be filtered before graph ingestion.
4. Pseudonymization uses HMAC-SHA-256 at ingestion. Reveal uses Shamir 2-of-3 threshold custody.
5. All synthetic test datasets must honor strict chronological ordering without future-data leakage.
6. The frontend targets a 3-screen layout:
   - Screen 1: Dual Timeline (raw vs attenuated + cumulative drift)
   - Screen 2: Graph with Risk Trajectory (React Flow causal subgraph)
   - Screen 3: Privacy Vault (Shamir 2-of-3 reveal ceremony + protected registry)