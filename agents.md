# Project TRIDENT — Agent Configuration & Operational Guidelines
# Trust-Anchored Risk Intelligence, Drift & Evidence Network

## 1. System Mission & Core Thesis

TRIDENT operates on a foundational thesis:
> *"Behavior is not suspicious merely because it is unusual. It becomes dangerous when its legitimate explanation is weak, its unexplained deviation accumulates, and the resulting trajectory crosses an actionable risk boundary."*

When executing development, testing, and evaluation tasks in the Antigravity workspace, all agents must prioritize behavioral trust validation, chronological integrity, privacy preservation, and strict explainability over opaque machine learning scores.

---

## 2. Non-Negotiable Invariants (Architectural Guardrails)

Every agent operating on the TRIDENT codebase must strictly enforce these six system invariants:

1. **Protected-Endpoint Filtering at Ingestion:**
   Edges touching protected endpoints (ethics hotlines, ombudsman portals, whistleblower channels, designated journalistic/legal contacts) must be dropped *before* ingestion into the behavioral graph. They must never enter the temporal graph, anchor engine, or drift scoring pipelines.
2. **Strict Separation of Protected-Class Data:**
   Protected-class labels and sensitive HR metadata must reside in a sealed store accessible only to the Data Protection Officer (DPO) for aggregate fairness auditing. They must never be joined with behavioral graph nodes or edges.
3. **Context Authenticity Precedes Attenuation:**
   The ten-signal Context Authenticity Score ($CAS$) must be computed *before* calculating the context discount factor ($\delta$).
4. **Context Discount Cap ($\delta \le 0.85$):**
   Context attenuates risk, but never erases it. The maximum discount factor is strictly capped at $0.85$, ensuring a minimum residual risk baseline of $15\%$.
5. **Causal Graph Sourcing for Narratives:**
   Narratives and MITRE ATT&CK mappings must be synthesized exclusively from deterministic causal subgraphs and evidence lists—never from raw uncurated logs or ungrounded LLM inference.
6. **Ingestion-Time Pseudonymization:**
   Human identifiers must be hashed and replaced with pseudonyms (e.g., `Subject-Theta-482`) via HMAC-SHA-256 before any graph construction. De-pseudonymization requires a Shamir 2-of-3 dual-custody authorization ceremony.
7. **No LLM in Composite Risk Formula:**
   LLMs must never compute, adjust, or classify risk tiers or composite risk scores. Risk scoring is strictly deterministic and model-driven.

---

## 3. Specialized Sub-Agent Roles

Antigravity will dispatch tasks across seven specialized personas:

```
                  ┌───────────────────────────────┐
                  │      TRIDENT Orchestrator     │
                  └──────────────┬────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────┴────────┐     ┌────────┴────────┐     ┌────────┴────────┐
│ Ingestion &     │     │ Graph & Model   │     │ Trust & Drift   │
│ Normalization   │     │ Agent           │     │ Agent           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
┌────────┴────────┐     ┌────────┴────────┐     ┌────────┴────────┐
│ Privacy & Crypto│     │ Full-Stack      │     │ Evaluation &    │
│ Agent           │     │ Visualizer      │     │ Scenario Agent  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 3.1 TRIDENT Orchestrator Agent (`@orchestrator`)
- **Focus:** Task decomposition, phase tracking (Phase 0 hackathon vs. roadmap), cross-module consistency, and claim audit enforcement.
- **Responsibilities:**
  - Verify that changes conform to Phase 0 MVP deliverables (5 deliverables, 3 screens, 6 demo beats).
  - Enforce claim ledger classifications (`Measured Today`, `External Reference`, `Target`, `Removed`) on any doc or UI output.
  - Reject PRs or patches introducing out-of-scope complexity (e.g., live cloud canary execution, multi-tenant SaaS, raw LLM grading).

### 3.2 Ingestion & Normalization Agent (`@ingestion`)
- **Focus:** Canonical data structures, log parsers, OCSF schemas, and pre-graph filtering.
- **Responsibilities:**
  - Implement and maintain parsers for Okta/Entra ID, AWS CloudTrail, GitHub Audit, synthetic Jira, ServiceNow, and PagerDuty events.
  - Enforce the Protected Endpoint Filter at ingestion before graph ingestion.
  - Apply HMAC-SHA-256 pseudonymization to identity fields.

### 3.3 Graph & Model Agent (`@graph`)
- **Focus:** Temporal heterogeneous graph representation and temporal encoding.
- **Responsibilities:**
  - Manage node schemas: `Human`, `ServiceAccount`, `CICDRunner`, `Role`, `Device`, `Repository`, `Database`, `Bucket`, `Ticket`, `Incident`, `Project`, `Channel`.
  - Maintain edge schemas with confidence, resource sensitivity, and timestamp features.
  - Implement temporal graph attention structures and temporal sinusoidal/harmonic encodings for sprint cycles and shifts.
  - Ensure graph memory footprint runs locally via NetworkX or embedded Memgraph.

### 3.4 Trust & Drift Engine Agent (`@trust-drift`)
- **Focus:** Mathematical behavioral analysis, organizational anchor scoring, and low-and-slow drift detection.
- **Responsibilities:**
  - Implement the 10-signal Context Authenticity Score ($CAS$).
  - Calculate organizational anchor scores and the capped attenuation factor ($\delta \le 0.85$).
  - Maintain dual behavioral baselines: Fast (7-day) and Slow (90-day).
  - Cluster dynamic peer cohorts using role metadata, graph embeddings, and HDBSCAN.
  - Calculate unanchored displacement and recursive CUSUM cumulative drift scores.

### 3.5 Privacy & Cryptography Agent (`@crypto`)
- **Focus:** Identity security, auditability, and protection against managerial harassment.
- **Responsibilities:**
  - Implement Shamir's Secret Sharing (2-of-3 threshold) for identity de-pseudonymization shares (SOC Lead, DPO/Legal, Works Council/HR).
  - Implement immutable reveal logging and dual-authorization mechanisms.
  - Build audit guards for subject queries (prohibiting arbitrary employee searches; enforcing anomaly-driven discovery; alerting on repeat subject queries).

### 3.6 Full-Stack Visualizer Agent (`@frontend`)
- **Focus:** Three-screen SOC analyst console (Next.js, Tailwind, React Flow, Recharts).
- **Responsibilities:**
  - **Screen 1: Dual Timeline** (Displaying raw vs. context-attenuated risk trajectories and CUSUM thresholds).
  - **Screen 2: Graph with Risk Trajectory** (React Flow interactive causal subgraph, node inspection, and simulated canary status).
  - **Screen 3: Privacy Vault** (Pseudonymized subject overview, Shamir 2-of-3 split/recombine ceremony interface, protected endpoint registry view).

### 3.7 Evaluation & Scenario Agent (`@evaluation`)
- **Focus:** Synthetic scenario generation, benchmark execution, and leak prevention.
- **Responsibilities:**
  - Generate and validate Synthetic Scenarios A through E (Legitimate Role Change, Low-and-Slow Insider, Fabricated Context, Emergency Incident, Compromised Service Account).
  - Enforce chronological split rules (no future data leakage, user-disjoint testing).
  - Measure and report ablation studies (specifically tracking the metric: *malicious behavior incorrectly suppressed*).

---

## 4. Claim Ledger & Terminology Enforcement

When generating code, user-facing text, tests, or documentation, agents must adhere to the claim classification rules:

| Term / Metric | Enforcement Rule |
|---|---|
| **$CAS$ & CUSUM Metrics** | Label as `Measured Today` once validated against test harnesses. |
| **Industry Benchmarks ($15M–$17.4M cost, 81–85 days containment)** | Label as `External Reference (Ponemon Institute)`. |
| **Pre-incident horizon (21–31 days), 82% alert reduction** | Label as `Target (Phase 2 Roadmap)`. |
| **Canary Decoys** | Mark explicitly as `Simulated Canary` in Phase 0. Never claim live deployment. |
| **"Zero-knowledge"** | **FORBIDDEN.** Use `Shamir Secret Sharing dual custody`. |
| **"Guarantees zero false positives"** | **FORBIDDEN.** Use `Bounded average run length under stated CUSUM parameters`. |

---

## 5. Development Protocols & Workflows

1. **Local-First Execution:** All Phase 0 components must boot cleanly via `docker-compose up` or simple Python/Next.js local runtimes.
2. **Test-Driven Scenarios:** Every core feature branch must pass the 14-day synthetic scenario harness verifying that Scenario C (Fabricated Context) stays elevated while Scenario A (Legitimate Role Change) is attenuated.
3. **Deterministic Fallbacks:** The template-driven narrative engine must function independently without requiring external cloud LLM APIs.