# TRIDENT

## Trust-Anchored Risk Intelligence, Drift & Evidence Network

### Tagline

**Trust the context. Track the trajectory. Prove the threat.**

### One-Sentence Product Definition

TRIDENT is a privacy-preserving insider-risk intelligence platform that verifies whether organizational context is trustworthy, detects cumulative behavioral drift across human and non-human identities, and produces evidence-backed security decisions before a potential insider attack becomes a material incident.

### Core Thesis

> **Behavior is not suspicious merely because it is unusual. It becomes dangerous when its legitimate explanation is weak, its unexplained deviation accumulates, and the resulting trajectory crosses an actionable risk boundary.**

The operating flow:

**Technical telemetry plus business context → trust analysis → cumulative drift → risk trajectory → evidence confirmation → causal investigation → privacy-preserving action.**

---

# 1. Core Differentiator

Never pitch "we use graph neural networks."

Pitch:

> **"Existing security systems ask whether behavior is unusual. TRIDENT asks whether the explanation for that behavior is trustworthy, whether the unexplained deviation is accumulating, and whether we can obtain evidence before the breach."**

Three mechanisms distinguish TRIDENT from every incumbent in this category:

1. **Trust-weighted organizational anchors with a Context Authenticity Score.** A ticket is not truth. It is a claim, and claims are scored.
2. **Cumulative unanchored drift.** Low-and-slow attacks are detected as accumulation, not as isolated spikes.
3. **Evidence before breach.** Risk trajectory predicts next assets; canary confirmation converts probabilistic suspicion into deterministic proof.

Two safeguards no competitor publicly shows:

- **Managerial-harassment protection.** Investigations begin from graph anomalies, not named individuals; subject selection is audited.
- **Whistleblower shielding.** Protected endpoints are filtered at ingestion, before the behavioral graph exists.

---

# 2. Why This Wins

TRIDENT wins because it survives the three questions a strict judge panel always asks:

1. **"What is the one idea?"** — *Is this behavior organizationally anchored, and is the anchoring trustworthy?*
2. **"What if the context is fabricated?"** — The ten-signal Context Authenticity Score. A ticket created four minutes before an anomaly, approved by the same reporting line, with no downstream commits, does not suppress risk.
3. **"What if the context is real?"** — The discount factor is capped at 0.85. Context attenuates risk, never erases it. A malicious insider cannot hide behind a genuine-looking ticket.

The plan also survives the quieter questions:

- **"How do you avoid dataset leakage?"** — Chronological splits, user-disjoint training, no future anchors, published experiment logs.
- **"What actually runs today?"** — Five deliverables, three screens, one vertical slice.
- **"Is this spyware?"** — Shamir dual custody, pseudonymized SOC, protected-endpoint filtering at ingestion, DPO-run fairness audits.

---

# 3. Product Objectives

TRIDENT solves six problems.

### 3.1 Context blindness

Distinguish legitimate role and project changes from unexplained behavioral deviations.

### 3.2 Low-and-slow attacks

Detect small actions that become dangerous only when accumulated over time.

### 3.3 Context manipulation

Detect fabricated, stale, contradictory, or abused business justifications rather than blindly trusting tickets and approvals.

### 3.4 Explainability

Give analysts the evidence chain behind an alert rather than a black-box risk score.

### 3.5 Privacy and misuse

Prevent security tooling from becoming a mechanism for arbitrary employee surveillance.

### 3.6 Identity expansion

Support human identities and non-human identities — service accounts, CI/CD runners, API keys — in version 1, with autonomous AI-agent coverage in Phase 4.

---

# 4. Product Architecture

TRIDENT consists of seven logical layers.

**Layer 1 — Signal Sources.** Identity providers, cloud audit trails, source control, ticketing, incident management, HRIS, communication platforms, calendars.

**Layer 2 — Event Normalization.** OCSF-style canonical events. Entity resolution. Timestamp normalization. Protected-endpoint filtering.

**Layer 3 — Temporal Graph.** Humans, non-human identities, roles, devices, repositories, databases, buckets, tickets, incidents, channels, service accounts.

**Layer 4 — Trust Engine.** Organizational anchor score. Context Authenticity Score. Authority, approval, temporal, and scope validation.

**Layer 5 — Drift Engine.** Temporal graph attention. Peer cohorts. Fast and slow baselines. Cumulative unanchored drift detection.

**Layer 6 — Evidence Engine.** Risk trajectory prediction. Canary layer (simulated in v1, live in Phase 2). Counterfactual analysis. Minimal evidence subgraph.

**Layer 7 — Investigation and Response.** Evidence timeline. MITRE mapping. Narrative synthesis. Privacy vault. SOAR actions.

---

# 5. Identity Model

TRIDENT represents the enterprise as a temporal heterogeneous graph.

### Node types

Human. Service account. CI/CD runner. API key. Role. Device. Repository. Database. Bucket. Ticket. Incident. Project. Channel. Calendar event. Approval. Credential.

### Edge types

Accessed. Queried. Modified. Assigned. Approved. Reviewed. Invited. Authenticated. Invoked. Delegated. Staged. Transferred. Connected to. Member of.

### Edge attributes

Every edge carries its source entity, target entity, relationship type, timestamp, source system, confidence score, and a feature vector including bytes transferred, session duration, IP risk, and resource sensitivity.

---

# 6. Event Normalization

All telemetry enters through an OCSF-style canonical event representation. Every event carries: entity, action, resource, timestamp, source, session, device, network context, resource sensitivity, business context, and identity context.

### Ingestion scope — Hackathon

Identity events from Okta or Entra. AWS CloudTrail-style events. GitHub-style audit events. Synthetic Jira. Synthetic ServiceNow. Synthetic PagerDuty.

### Ingestion scope — Production

Workday. Azure AD or Entra. AWS. GCP. GitHub or GitLab. Slack or Teams. Jira or Linear. ServiceNow. PagerDuty. Google Calendar or Outlook.

---

# 7. Protected Endpoint Filter

Privacy-sensitive endpoints must be removed from behavioral aggregation before entering the graph.

Protected examples: ethics hotline, ombudsman, whistleblower portal, external counsel, protected disclosure channels, designated journalistic contacts.

### Processing rule

Every raw event is checked at ingestion. If the target is protected, the event goes to an audit-only privacy stream and is excluded from the behavioral graph. If the target is not protected, the event continues through normal processing.

The filter operates before graph construction, so protected activity cannot influence behavioral scoring.

**Admin tamper-proofing:** attempts by security administrators to remove endpoints from the protected registry are logged and require dual authorization.

---

# 8. Data Flow Invariants

Six rules make the architecture safe. They are non-negotiable.

1. **Protected-endpoint edges are dropped at ingestion, before the graph is built.**
2. **Protected-class labels never enter the behavioral graph.** They live in a sealed store, accessible only to the DPO, used solely for aggregate fairness auditing.
3. **Context Authenticity Score is computed before the discount factor.**
4. **Discount factor is capped at 0.85.** Context never erases risk.
5. **Narrative generation reads from the causal subgraph, not raw logs.**
6. **Pseudonymization happens at ingestion, not at query time.**

---

# 9. Trust Layer

The trust layer converts "a ticket exists" into "the ticket is a trustworthy explanation."

## 9.1 Organizational Anchor

For every suspicious activity edge, TRIDENT finds candidate organizational anchors, evaluates each one, and selects the highest-trustworthy anchor.

Candidate anchors include: Jira ticket, ServiceNow request, PagerDuty incident, HR role change, GitHub assignment or pull request, calendar event, approved project membership, managerial assignment.

## 9.2 Context Authenticity Score

A contextual justification must itself be validated. TRIDENT uses ten initial signals.

1. **Temporal mismatch** — ticket created immediately before suspicious activity.
2. **Approver conflict** — requester and approver relationship is suspicious.
3. **Emergency-change abuse** — abnormal emergency ticket frequency.
4. **Separation-of-duties violation** — conflicting requester, approver, and resource relationships.
5. **Stale HR metadata** — organizational metadata no longer aligns with behavior.
6. **Scope mismatch** — ticket semantics do not match accessed resource.
7. **Cross-signal inconsistency** — missing corroboration from source control, communication, or calendar.
8. **Ticket velocity anomaly** — abnormal burst of ticket creation.
9. **Ghost ticket** — no downstream engineering or business artifact.
10. **Post-hoc modification** — ticket edited after the suspicious event.

The Context Authenticity Score is a sigmoid over the weighted sum of these ten normalized signals. Phase 0 uses hand-tuned weights via configuration. Phase 1 calibrates weights on the CMU CERT dataset plus synthetic fabrication scenarios.

## 9.3 Anchor Score

The anchor score for an event is the maximum over candidate anchors of four multiplied components: the anchor's organizational authority weight, its Context Authenticity Score, its semantic scope match with the accessed resource, and its temporal decay since creation.

This structure prevents "a ticket exists" from becoming "the activity is legitimate."

## 9.4 Context Attenuation

The context discount factor is one minus the product of a scaling coefficient and the anchor score. The scaling coefficient is capped between zero and 0.85.

Consequence:

- Maximum risk reduction is 85%.
- Minimum residual risk is 15%.

No business context can completely erase behavioral risk.

---

# 10. Drift Layer

## 10.1 Temporal Behavioral Model

Continuous-time heterogeneous graph model with temporal graph attention. Components: node embeddings, edge embeddings, time encoding, causal temporal masking.

Time representation uses sinusoidal and harmonic encoding to capture weekly cycles, shift schedules, sprint cycles, and repeated operational behavior.

## 10.2 Behavioral Baselines

Two baselines run in parallel.

**Fast baseline — 7 days.** Purpose: acute behavioral changes.

**Slow baseline — 90 days.** Purpose: structural behavioral profile and resistance to baseline poisoning.

Comparison is against both the individual baseline and the dynamic peer cohort.

## 10.3 Dynamic Peer Cohorts

Cohorts are formed by clustering on role metadata, resource topology, temporal behavior, graph embeddings, and team or project structure. Examples: backend engineers, SRE, finance operations, security engineers, database administrators, DevOps, support.

A user behaving differently from the company average is not automatically abnormal. The question is: is the user deviating from comparable peers?

## 10.4 Unanchored Displacement

For each behavioral step, the unanchored displacement is the product of the context discount factor and the Euclidean distance between the current user embedding and the user's baseline embedding.

Interpretation: high behavioral deviation combined with low contextual justification produces high unanchored displacement.

## 10.5 Cumulative Drift

The cumulative drift score follows a CUSUM-style recursion. It starts at zero. At each step it takes the maximum of zero and the previous score plus the current displacement minus a baseline drift rate minus an allowance parameter.

An alert is raised when the cumulative score exceeds a calibrated threshold.

Inputs: individual baseline, peer baseline, anchor score, context authenticity, time, resource criticality, behavioral displacement.

Outputs: drift score, drift velocity, trajectory, threshold state.

This catches the attack legacy UEBA misses: five files a day for four months.

---

# 11. Composite Risk

Composite risk is the product of five factors:

- Behavioral anomaly score.
- Contextual uncertainty, defined as one minus the product of the discount factor and the anchor score.
- Cumulative drift.
- Resource criticality.
- Identity risk (human or non-human).

**Invariant:** No LLM output enters this formula. The LLM never decides risk, severity, or containment. Only deterministic and model-based components do.

---

# 12. Risk Tiers

### Tier 1 — Contextual Drift

Low risk. Strong trusted context. No meaningful cumulative drift. Action: update baseline, no SOC action.

### Tier 2 — Unanchored Exploration

Medium cumulative drift. Weak or absent context. Action: SOC review, step-up authentication recommendation, continue monitoring.

### Tier 3 — High-Risk Trajectory

High drift. Cross-boundary movement. Sensitive resources. Low Context Authenticity. Action: revoke temporary credentials, forensic snapshot, SOC escalation.

### Tier 4 — Critical

Confirmed or high-confidence evidence. Bulk exfiltration. Critical resource compromise. Action: isolate endpoint, revoke credentials, freeze destination, CISO and legal escalation.

---

# 13. Evidence Layer

## 13.1 Evidence Engine

Production flow: risk trajectory → predict likely next resource → choose safe evidence mechanism → canary or decoy → observe interaction → increase evidence confidence.

Hackathon flow: risk trajectory → predicted target → simulated canary event → evidence confirmation state.

The hackathon demo claims a simulated canary. It does not claim live canary deployment.

## 13.2 Counterfactual Engine (Phase 2)

An analyst can pose a hypothetical: "What if this user was assigned to Project Apollo?"

The system recomputes Context Authenticity, anchor score, discount factor, drift, cumulative drift, and composite risk.

Output format: percentage of drift explained, percentage of drift unexplained, list of remaining suspicious behavior.

## 13.3 Causal Evidence Graph

The system extracts a minimal suspicious subgraph rather than presenting the entire enterprise graph.

The typical chain: credential anomaly → privilege expansion → unusual resource discovery → sensitive data access → staging → outbound destination.

Each edge in the subgraph carries its timestamp, source, confidence, resource, context, and reason.

---

# 14. Investigation Layer

## 14.1 Narrative Engine

The narrative engine receives the causal subgraph, timeline, anchor results, drift metrics, and evidence list. It produces an executive summary, observed timeline, context validation, residual unexplained behavior, MITRE mappings, recommended actions, and evidence references.

Generation strategy: template-first generation, with optional local LLM polishing.

The on-prem LLM is a quantized Mistral-7B-Instruct served via vLLM. This choice is deliberate: it satisfies air-gapped sovereign deployment without cloud API dependency.

The LLM cannot introduce unsupported facts. Every sentence must be traceable to evidence.

## 14.2 MITRE Mapping

Example mappings: T1078 (Valid Accounts), T1068 (Exploitation for Privilege Escalation), T1005 (Data from Local System), T1567 (Exfiltration Over Web Service).

Mappings are generated from deterministic rules and model evidence, not free-form LLM guessing.

---

# 15. Privacy and Fairness

## 15.1 Pseudonymization

Raw identity is converted to a pseudonymous subject ID at ingestion. Example: employee identifier is replaced by a subject token such as THETA-482 before any graph construction.

The SOC never sees the original identifier during normal investigation.

## 15.2 Shamir Dual Custody

The master secret is split into three shares.

- Share A is held by the SOC Lead.
- Share B is held by the DPO or Legal.
- Share C is held by the Works Council or HR.

Any two shares authorize identity reveal.

Every reveal logs immutably: request, timestamp, reason, authorizers, subject, result.

## 15.3 Managerial-Harassment Protection

**Failure mode:** a biased manager uses the tool to surveil or target a specific subordinate.

**Mechanism:**

- SOC analysts see only pseudonyms and behavioral graphs. They do not see manager identity, reporting line, gender, race, seniority, or personal identifiers.
- No user-facing query interface allows "show me everything about Alice." Investigations begin from graph anomalies, trajectories, resources, or attack patterns — not from named employees.
- **Subject-selection audit:** if a named individual is manually selected as investigation subject, the action is flagged for DPO review.
- **Repeat-subject guard:** if the same pseudonym appears as investigation subject more than a configured number of times in a rolling window without a Tier 3 or Tier 4 outcome, the pattern is surfaced to the DPO.
- Manager-level access to any per-individual behavioral view is prohibited by design. Managers see team-level aggregates only.

## 15.4 Whistleblower Shielding

**Failure mode:** the platform accidentally aggregates whistleblower activity — contact with ombudsman, ethics hotline, or protected disclosure channels — into a risk surface, chilling protected activity.

**Mechanism:**

- Configurable protected endpoint registry: ombudsman endpoints, ethics hotline domains, external counsel addresses, journalistic contact points, internal disclosure channels.
- Any edge touching a protected endpoint is excluded from graph aggregation and never enters the anchor score, drift score, or narrative.
- The exclusion is enforced at the ingestion layer, not the query layer. Protected activity never enters the graph.
- The exclusion list is managed jointly by the DPO and the Works Council, not by security.
- Attempts by security administrators to remove endpoints from the protected registry are logged and require dual authorization.

## 15.5 Neurodiversity Normalization

Baselines are cohort-relative, not global. Off-hours work is evaluated against sprint deadlines and PR merge queues, not against a 9-to-5 norm. Developers, SREs, and international teams working flexible or non-standard schedules are not penalized for the shape of their work.

## 15.6 Disparate-Impact Monitoring with Data Boundary

Protected-class data is held in a sealed store accessible only to the DPO. It is never joined to the behavioral graph. It is used solely for aggregate fairness auditing. The SOC never sees it. The audit is run by the DPO, not by security.

---

# 16. Competitive Positioning

| Capability | TRIDENT | Exabeam | DTEX InTERCEPT | Cyberhaven DDR | Microsoft Purview Insider Risk |
|---|---|---|---|---|---|
| ML foundation | Temporal graph + CUSUM | Static profiling + rules | Endpoint heuristics | Content lineage | Static rule templates |
| Trust-weighted anchors | Yes, with Context Authenticity Score | Manual rule suppression | Basic HR attributes | Content lineage only | Native M365 signals only |
| Fabricated-context detection | Ten-signal scoring | Not described | Not described | Not described | Not described |
| Cumulative low-and-slow | CUSUM over unanchored displacement | Limited | Post-execution endpoint tracking | Immediate exfiltration interception | Post-violation trigger |
| Non-human and agentic AI coverage | NHI in v1; agentic AI in Phase 4 | Human + basic service accounts | Endpoints + humans | Data assets + humans | M365 users only |
| Privacy model | Shamir 2-of-3 dual custody | Standard RBAC | Basic cloud pseudonymization | Identifier obfuscation | Single-admin pseudonymization |
| Active deception | Phase 2 | None | None | None | None |
| Whistleblower shielding | Core v1 | Not described | Not described | Not described | Not described |
| Managerial-harassment protection | Core v1 | Not described | Not described | Not described | Not described |

**Honesty note:** "Not described" means we could not find public documentation of that capability. It does not mean the capability does not exist. Our own roadmap rows are labeled as roadmap.

---

# 17. MVP Scope

## 17.1 Five Deliverables

1. **Telemetry and OCSF normalization** — Okta-like, CloudTrail-like, synthetic Jira, synthetic ServiceNow.
2. **Temporal graph** — human, service account, CI/CD runner, repo, database, bucket, ticket, incident.
3. **Trust engine** — authority, temporal validity, scope similarity, approver relationship, corroboration, ghost-ticket detection, post-hoc modification detection, Context Authenticity Score.
4. **Cumulative drift** — fast baseline, slow baseline, peer comparison, unanchored displacement, cumulative drift score.
5. **SOC interface** — three screens.

## 17.2 Three Screens

1. Dual Timeline.
2. Graph with Risk Trajectory.
3. Privacy Vault.

## 17.3 Supported Identity Types in v1

Human. Service account. CI/CD runner.

No AI-agent modeling in v1.

## 17.4 Canary Scope

Simulated only. The decoy bucket is shown in the interface, not deployed in the environment. Live canaries are Phase 2.

## 17.5 Explicitly Out of Phase 0

- Counterfactual sandbox (Phase 2).
- Live canary injection (Phase 2).
- Agentic AI baselines (Phase 4).
- Multi-tenant SaaS (Phase 3).
- On-prem LLM narrative (Phase 1; v1 uses templates).

---

# 18. Technology Stack

## Backend

Python. FastAPI. Pydantic. NumPy. Pandas or Polars. PyTorch. PyTorch Geometric. scikit-learn. HDBSCAN.

## Graph

NetworkX for the hackathon, or Memgraph if the team is already familiar.

## Storage

SQLite or PostgreSQL. Parquet. Redis optional.

## Frontend

Next.js. React. TypeScript. Tailwind. React Flow. Recharts.

## Security

Python cryptography library. Shamir Secret Sharing implementation. HMAC-SHA-256 pseudonymization.

## Deployment

Docker Compose. No Kubernetes during the hackathon.

---

# 19. Synthetic Scenario Generator

Create controlled enterprise scenarios.

**Scenario A — Legitimate role change.** Promotion leads to new Jira assignments, new repository access, new database access, and peer-group migration. Expected outcome: low risk.

**Scenario B — Low-and-slow insider.** Resource discovery, permission exploration, unrelated repository access, sensitive database queries, and staging. Expected outcome: gradually increasing cumulative drift.

**Scenario C — Fabricated context.** Suspicious access preceded by a ticket created four minutes earlier, same requester and approver, no downstream artifacts, scope mismatch. Expected outcome: Context Authenticity Score low; risk remains elevated.

**Scenario D — Emergency incident.** PagerDuty incident triggers off-hours admin, emergency database changes, high-volume activity. Expected outcome: risk attenuated.

**Scenario E — Compromised service account.** Normal CI/CD activity shifts to unexpected destination, abnormal API pattern, privilege escalation. Expected outcome: non-human identity risk increases.

---

# 20. Evaluation Protocol

Do not merely report AUC. Run ablations.

**Experiment 1 — Baseline.** Isolation Forest or rules.

**Experiment 2 — Temporal graph only.**

**Experiment 3 — Temporal graph plus organizational context.**

**Experiment 4 — Plus Context Authenticity Score.**

**Experiment 5 — Plus cumulative drift.**

Compare: AUC, precision, recall, false positive rate, F1, detection horizon, alert reduction.

The most important metric: **malicious behavior incorrectly suppressed.** This metric is measured directly and reported. It is the one a judge will ask about.

---

# 21. Dataset Split Rules

Use chronological splits.

Ensure: no future activity enters embeddings, no future ticket context, no test-user leakage, hyperparameter tuning only on validation data.

All experiment logs are published alongside the results.

---

# 22. Claim Ledger

Every number shown in the demo carries one of four labels: **Measured Today**, **External Reference**, **Target**, or **Removed**.

| Claim | Label | Source / Status |
|---|---|---|
| $15M–$17.4M average annual insider incident cost | Verified external statistic | Ponemon Cost of Insider Threats, recent editions |
| 81–85 day average containment time | Verified external statistic | Ponemon Cost of Insider Threats, recent editions |
| ~82:1 to ~109:1 non-human-to-human identity ratio | Verified external statistic | Palo Alto Networks Identity Security Landscape |
| CMU CERT r5.2 AUC 0.9924 | External reference — not our result | Published literature. Not reproduced by us. Cannot be cited as our performance. |
| 21–31 day pre-incident horizon | Target | Phase 2 goal. Not yet measured by us. |
| 82% alert-fatigue reduction | Target | Phase 2 pilot goal. Not a fact. |
| Sub-4-hour mean time to detect | Target | Phase 2 pilot goal. Not a fact. |
| "Zero-knowledge" privacy vault | Not used | We use Shamir Secret Sharing, not zero-knowledge proofs. We say what we do. |
| "Mathematically guarantees near-zero false positives" | Not used | Replaced with: "CUSUM provides bounded average run length under stated assumptions." |
| 100% Works Council approval rate | Removed | Cannot be claimed before any deployment. |

**Demo-day rule:** every number on screen carries one of the four labels. No exceptions.

---

# 23. Demo Data

Pre-load one complete 14-day scenario. Six anchor events drive the six demo beats.

**Days 1–4 — Baseline.** Normal activity.

**Day 5 — Legitimate new project.** Jira assignment to a new domain. Platform suppresses. This is the benign-anomaly beat.

**Day 9 — Silent drift begins.** Unusual repo access, new S3 access, privilege change. No anchor. Cumulative drift rises.

**Day 10 — Fabricated Jira ticket.** Ticket created four minutes before EU payroll database access. Same requester and approver. No downstream artifacts. Context Authenticity Score low. Risk not suppressed.

**Day 12 — Sensitive staging.** Data staging to temporary memory mount. Predicted canary target.

**Day 13 — Simulated canary trip.** Evidence confirmation state transitions to confirmed.

**Day 14 — Escalation.** Dual-custody unlock. Identity revealed. Audit log.

The remaining eight days carry background traffic and benign noise. They exist in data; they do not appear on screen.

---

# 24. Demo Script — Six Beats

**0:00–0:30 — Hook.** Insider breaches take 81 to 85 days to contain and cost $15M to $17.4M. Existing tools drown SOCs in false positives. TRIDENT answers one question: is the explanation for this behavior trustworthy?

**0:30–1:30 — Benign anomaly suppressed, then silent drift begins.** Legacy flags prod database access at 94 out of 100. TRIDENT checks Jira #841 and PagerDuty — anchor score 0.94, discount 0.04, suppressed. Then the same actor touches unassigned repos and S3. No anchor. Cumulative drift begins to climb on screen.

**1:30–2:30 — Fabricated context detection.** Actor creates a Jira ticket four minutes before accessing the EU payroll database. TRIDENT flags temporal mismatch (signal 1), no downstream commits (signal 9), approver in the same reporting line (signal 4). Context Authenticity Score is 0.21. Risk is not suppressed. This is the beat that proves the mechanism.

**2:30–3:30 — Canary trip and causal narrative.** Simulated canary bucket triggered. Dossier maps: credential anomaly, privilege expansion, repo discovery, staging, outbound channel. MITRE T1078, T1068, T1005, T1567.

**3:30–4:30 — Privacy and fairness.** SOC sees Subject-Theta-482. CISO and Legal submit Shamir shares. Identity revealed. Audit logged. Whistleblower-shielded endpoint shown as excluded from aggregation.

**4:30–5:00 — Close.** Context attenuates risk. Fabricated context is itself a signal. Unanchored drift accumulates. Deception confirms. Privacy protects.

---

# 25. Narrative Output

An example incident dossier contains:

- **Subject** — the pseudonymous identifier.
- **Risk** — the composite risk tier.
- **Trajectory** — the cumulative drift classification.
- **Context** — whether an organizational justification was detected.
- **Context Authenticity** — the score classification.
- **Reason** — the specific signals that degraded the anchor.
- **Observed sequence** — the ordered chain of behavioral steps.
- **Evidence** — counts of graph events, identity events, contextual inconsistency clusters, and canary confirmations.
- **Recommended response** — the tiered actions appropriate to the severity.

---

# 26. Risks, Cons, and Mitigations

| Risk / Con | Why It Matters | Mitigation |
|---|---|---|
| Fabricated context | Insiders can create tickets or abuse emergency changes | Ten-signal Context Authenticity Score with named signals |
| Context over-trust | A strong anchor could zero out real risk | Discount factor capped at 0.85 |
| Dataset leakage | Inflated metrics destroy credibility | Chronological splits; user-disjoint training; published experiment logs |
| LLM hallucination | False narratives in forensic reports | Deterministic narrative; LLM polish only; evidence citations required |
| Canary legal risk | Decoys could entrap or disrupt legitimate work | Decoys only outside legitimate workflow; legal review; no entrapment |
| Privacy backlash | Works Councils may veto deployment | Shamir dual custody; pseudonymized SOC; whistleblower shielding; DPO-run fairness audits |
| Overclaiming | Judges and buyers punish unsupported claims | Claim ledger; four-label rule on all demo numbers |
| Scope creep | Too many subsystems to demo reliably | Five deliverables, three screens, six beats |
| NHI and AI blind spot | Modern attacks use service accounts and agents | NHI in v1; agentic AI in Phase 4 |
| Alert fatigue | SOC ignores noisy tools | Anchor suppression plus cumulative drift plus canary confirmation |
| Adoption resistance | Security teams distrust new UEBA | Open-core CLI; CTF; transparent benchmarks; pilot deployments |
| Compliance overstatement | Claiming certifications not held | Regulatory readiness phased honestly |
| Uncalibrated weights in v1 | Hand-tuned weights may misjudge edge cases | Hand-tuned in Phase 0; calibrated on CERT plus synthetic fabrication in Phase 1 |
| Canaries deferred to Phase 2 | The most novel mechanism is not in v1 | Demo simulates it explicitly; claims labeled accordingly |
| Named competitors are well-funded | Distribution advantages we do not have | Wedge on fabricated-context detection and whistleblower shielding |

---

# 27. Regulatory Readiness

### Currently held

None. No certifications today. No pilot deployments today. No Works Council approvals today.

### Architectural alignment (built in from day one, not certified)

- GDPR Article 25 (data protection by design).
- GDPR Article 32 (security of processing).
- GDPR Article 88 (processing in employment context).
- BetrVG §87 (German Works Council co-determination).

### Target by phase

- SOC2 Type I — Phase 2, Months 4 to 6.
- SOC2 Type II and ISO 27001 — Phase 3, Months 7 to 12.
- GDPR Article 25/35 DPIA and Works Council package — Phase 3.
- EU AI Act, DORA, NIS2 alignment — Phase 3.
- ISO 42001 — post-general-availability.

Every mention of compliance uses "targeted by Phase X" or "architecturally aligned." Never "ready" or "compliant."

---

# 28. Production Roadmap

### Phase 0 — Hackathon (Weeks 1–4)

OCSF normalization. Temporal graph. Context Authenticity Score. Cumulative drift. Three-screen dashboard. Shamir. Synthetic evidence.

### Phase 1 — Alpha (Months 1–3)

Kafka or Flink. Memgraph. Production PyG model. Full Context Authenticity signals. Real connector fabric. LLM narrative version zero. SOC2 Type I preparation begins.

### Phase 2 — Enterprise Beta (Months 4–6)

Predictive canaries. Counterfactual sandbox. SOAR integration. Real SIEM integrations. Shamir production hardening. Three pilot deployments in fintech, healthcare, and defense. SOC2 Type I certified.

### Phase 3 — General Availability (Months 7–12)

Multi-tenant SaaS. Multi-region clusters. HSM integration. Non-human and agentic AI coverage. SOC2 Type II and ISO 27001 certified. GDPR Article 25/35 DPIA package and Works Council package. EU AI Act, DORA, NIS2 alignment documented. MDR and MSSP channel partnerships.

### Phase 4 — Agentic Security (Post-GA)

AI-agent behavioral baselines. Prompt injection detection. Tool-use anomaly detection. Agent-to-resource graph. Confused-deputy detection. Federated learning.

---

# 29. Commercial Model

### Community

Free. CLI. OCSF parser. Single-node graph. Basic anomaly analysis.

### Essential

$5 per human identity per month. $0.75 per non-human identity per month. Cloud and identity telemetry. Graph monitoring. 14-day retention.

### Enterprise

$10 per human per month. $1.50 per non-human per month. Full context. Context Authenticity Score. Cumulative drift. Privacy vault. LLM narratives. 365-day history. SOAR.

### Sovereign

$18 per human per month. $3 per non-human per month. Air-gapped. HSM. Custom model. Dedicated SLA.

### Return on Investment

For 5,000 humans and 50,000 non-human identities: enterprise cost is approximately $600k plus $900k, totaling $1.5M per year.

Preventing one $17.4M insider incident pays for 11 years of platform.

Preventing a single mid-level IP exfiltration pays back in year one.

---

# 30. Target Customers

### Primary verticals

FinTech. Healthcare. Cloud SaaS. Defense. Critical infrastructure. Large enterprises.

### Buyer

CISO. VP Security.

### Users

SOC Tier 2 and Tier 3. Threat hunters. Insider risk investigators. IAM. Cloud security.

### Approvers

DPO. General Counsel. HR. Works Council. Compliance.

---

# 31. Open-Core Strategy

Release a free CLI tool.

Features: local Git privilege analysis, AWS IAM drift analysis, OCSF parser, baseline comparison, synthetic benchmark tools.

Funnel: CLI → Community → Benchmark → CTF → Enterprise POC → TRIDENT platform.

---

# 32. Judge Q&A Preparation

**Q: What if an insider fabricates a Jira ticket?**
A: The ten-signal Context Authenticity Score detects temporal mismatch, approver conflict, ghost tickets, and post-hoc modification. A fabricated ticket reduces risk far less than a genuine one. Discount factor is also capped at 0.85, so even a strong anchor cannot zero out risk.

**Q: How do you avoid dataset leakage?**
A: Chronological splits, user-disjoint training, no future anchors in embeddings, hyperparameter tuning only on validation data. Experiment logs are published.

**Q: Is this GDPR compliant?**
A: Architecturally aligned with Articles 25, 32, and 88. Not certified. Shamir dual custody. Protected-class data in sealed DPO-only store. DPO-run fairness audits. Works Council co-determination package in Phase 3.

**Q: What actually works today?**
A: Five Phase 0 deliverables: OCSF parser, temporal graph, trust engine with Context Authenticity Score, cumulative drift, three-screen SOC interface with Shamir unlock. Canaries are simulated, and labeled as such.

**Q: Why not Exabeam, DTEX, Cyberhaven, Purview?**
A: None publicly documents fabricated-context detection or whistleblower shielding. None covers non-human and agentic AI as unified graph entities. Privacy model differs: Shamir 2-of-3 versus single-admin or RBAC.

**Q: How does this avoid becoming spyware?**
A: Investigations begin from graph anomalies, not named individuals. Subject-selection audited. Managers see team aggregates only. Protected endpoints filtered at ingestion. Unmasking requires 2-of-3 quorum.

**Q: What if the canary triggers on legitimate activity?**
A: Canaries are only placed in resources with no legitimate workflow. Interaction is defined as a deterministic signal. Canaries are Phase 2 and scoped so that a false trip requires a legitimate user to touch a resource they have no reason to touch.

**Q: What if the business context itself is compromised?**
A: That is exactly the failure mode the Context Authenticity Score is designed for. Fabricated or abused context degrades the score. Combined with the 0.85 cap, compromised context cannot fully suppress risk.

**Q: Why should we trust your metrics?**
A: Every metric is labeled. Nothing is called "Demonstrated" unless we ran it. External references are labeled as external. Targets are labeled as targets. The claim ledger is public.

---

# 33. Final Architecture Overview

Telemetry and business context feed the temporal graph. The trust engine computes anchor score and Context Authenticity Score. Unanchored displacement feeds the cumulative drift trajectory. The risk state emerges from composite risk. The evidence engine predicts and confirms. The evidence graph isolates the causal chain. SOC investigation produces MITRE mapping and narrative. The privacy vault governs identity release. SOAR actions execute the response.

---

# 34. Build Priority

**P0 — Phase 0 must-haves.** Event normalization. Synthetic scenario generator. Temporal graph. Trust-Aware Anchor Engine. Context Authenticity Score. Cumulative drift. Risk engine. Dashboard. Shamir privacy demo.

**P1 — Phase 0 supporting.** Evidence simulator. MITRE mapping. Evidence-backed narrative. Peer cohorts. Protected endpoints.

**P2 — Phase 2.** Predictive canaries. Counterfactual sandbox. SOAR. SIEM. Enterprise connectors.

**P3 — Post-GA.** Agentic AI monitoring. Federated graph learning. Multi-tenant SaaS. Air-gapped deployment. HSM.

---

# 35. Final Checklist

- One sentence thesis: "Is the explanation for this behavior trustworthy?"
- One killer demo beat: fabricated-context detection via the ten-signal Context Authenticity Score.
- One differentiated mechanism: Trust-Aware Anchor Engine with Context Authenticity Score plus cumulative drift.
- One honest benchmark: external numbers labeled external; only our own runs labeled measured.
- One privacy primitive: Shamir 2-of-3 dual custody, correctly named.
- Two fairness mechanisms: managerial-harassment protection and whistleblower shielding, both with named mechanics.
- One competitive table: Exabeam, DTEX, Cyberhaven, Purview, with honest "not described" cells.
- One scoped MVP: five deliverables, three screens, six demo beats.
- One phased roadmap: four phases, twelve months.
- Zero overclaims. Zero self-graded perfect scores. Zero misattributed statistics. Zero future milestones described as present capability.

---

# 36. Closing Statement

TRIDENT is not another UEBA dashboard. It is a platform that verifies whether the explanation for behavior is trustworthy, measures whether unexplained deviation is accumulating, and produces evidence before the breach — all while keeping employee identity behind cryptographic dual custody.

The complete chain the hackathon demonstrates:

Legitimate anomaly leads to trusted context leads to suppression.

Then unexplained behavior leads to fabricated justification leads to low Context Authenticity leads to cumulative drift accumulation leads to high-risk trajectory leads to simulated evidence confirmation leads to an evidence-backed dossier leads to pseudonymous investigation leads to dual-custody identity release.

**TRIDENT**
**Trust. Trajectory. Evidence.**
**Trust the context. Track the trajectory. Prove the threat.**