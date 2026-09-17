# TRIDENT — Trust-Anchored Risk Intelligence, Drift & Evidence Network

> **"Behavior is not suspicious merely because it is unusual. It becomes dangerous when its legitimate explanation is weak, its unexplained deviation accumulates, and the resulting trajectory crosses an actionable risk boundary."**

---

## Overview

TRIDENT is a privacy-preserving insider-risk intelligence platform that verifies whether organizational context is trustworthy, detects cumulative behavioral drift across human and non-human identities, and produces evidence-backed security decisions before a potential insider threat becomes a material incident.

### Non-Negotiable Invariants
1. **Protected-Endpoint Filtering at Ingestion:** Edges touching ethics hotlines, ombudsman portals, or whistleblower channels are dropped *before* ingestion into the behavioral graph.
2. **Strict Separation of Protected-Class Data:** Protected HR metadata resides in a sealed store for DPO aggregate auditing only and never enters graph representations.
3. **Context Authenticity Precedes Attenuation:** The 10-signal Context Authenticity Score ($CAS$) is computed *before* calculating the context discount factor ($\delta$).
4. **Context Discount Cap ($\delta \le 0.85$):** Context attenuates risk, but never erases it. Minimum residual risk baseline of $15\%$ ($\delta \ge 0.15$).
5. **Causal Graph Sourcing for Narratives:** Incident dossiers and MITRE ATT&CK mappings are derived deterministically from causal subgraphs—never from raw ungrounded LLMs.
6. **Ingestion-Time Pseudonymization:** Identifiers are hashed and replaced with pseudonyms (e.g. `Subject-Theta-482`) via HMAC-SHA-256 before graph construction.
7. **Deterministic Mathematics:** Zero raw LLMs in risk calculation, CAS signal evaluation, or discount factors.

---

## 3-Screen SOC Analyst Console (Next.js + Tailwind + React Flow + Recharts)

### Screen 1: Dual Timeline
- Maps raw anomaly spikes alongside context-attenuated risk trajectories ($R_{raw}$ vs $R_{attenuated}$).
- Plots recursive CUSUM cumulative drift ($S_t$) with calibrated thresholds (Stable $\tau=0.8$, High Risk $\tau=2.0$, Critical $\tau=4.0$).
- 14-day interactive scrubber with hackathon demo beat callouts (Days 1–14).
- Daily telemetry inspection drawer displaying normalized canonical events and SHA-256 payload hashes.

### Screen 2: Graph with Risk Trajectory
- React Flow causal DAG showing actor, credentials, code repositories, databases, memory staging, and simulated canaries.
- Interactive Simulated Canary Deception control card: trigger decoy trip to transition confirmation state from `PROBABILISTIC` to `CONFIRMED`.
- Template-driven forensic incident dossier with chronological attack progression and MITRE ATT&CK matrix.
- 6-dimension z-score drift attribution bar chart.

### Screen 3: Privacy Vault & Governance
- Shamir 2-of-3 Dual-Custody Ceremony (SOC Lead, DPO/Legal, Works Council/HR) for unmasking real employee identities.
- Cryptographic hash-chained reveal ledger with mathematical SHA-256 verification.
- Anti-harassment safeguards: direct name/email search blocker and DPO repeat-subject inspection alerts.
- Ingestion protected-endpoint registry confirming 100% pre-graph isolation.

---

## Project Directory

```
project-trident/
├── backend/
│   ├── api/
│   │   ├── app.py                       # FastAPI application & CORS
│   │   ├── manager.py                   # ScenarioDemoManager singleton coordinator
│   │   └── routes/                      # Modular REST endpoints (timeline, graph, risk, canary, scenarios, evidence, privacy)
│   ├── common/                          # CanonicalEvent, Context, and CAS schemas
│   ├── crypto/
│   │   ├── shamir_vault.py              # Shamir 2-of-3 threshold vault & SHA-256 hash-chained ledger
│   │   └── harassment_audit.py          # Anti-harassment direct query block & DPO alerts
│   ├── drift/                           # Fast/slow baselines, cohort clustering, and recursive CUSUM
│   ├── evidence/                        # Simulated canary engine, causal extractor, and narrative dossier
│   ├── graph/                           # Continuous-time NetworkX graph and time-window slicer
│   ├── ingestion/                       # Protected filter, HMAC pseudonymizer, and OCSF normalizer
│   ├── risk/                            # Deterministic composite risk calculator (Tiers 1-4)
│   └── scenarios/                       # Scenarios A through E and 14-day master demo dataset
├── frontend/                            # Next.js 14 SOC Console
│   ├── src/
│   │   ├── app/                         # App router, globals.css, layout.tsx, page.tsx
│   │   ├── components/
│   │   │   ├── Header.tsx               # Brand banner, scenario picker, active beat indicator
│   │   │   ├── Screen1DualTimeline/     # Timeline chart, scrubber, and daily event drawer
│   │   │   ├── Screen2CausalGraph/      # React Flow DAG, canary card, dossier, and drift bars
│   │   │   └── Screen3PrivacyVault/     # Shamir ceremony, hash-chained log, and anti-harassment
│   │   └── lib/                         # API client, TypeScript contracts, and mock datasets
├── tests/                               # 17 comprehensive test suites covering all invariants
├── run_demo.ps1                         # Unified PowerShell demo runner
├── run_demo.bat                         # Unified Windows batch demo runner
├── requirements.txt
└── test.sh
```

---

## Running Project TRIDENT

### Option 1: Unified Quickstart
```powershell
# In PowerShell (launches backend and frontend concurrently)
.\run_demo.ps1
```
Or in Windows Command Prompt:
```cmd
run_demo.bat
```

### Option 2: Running Components Individually

**Backend (FastAPI):**
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:3000** in your browser to interact with the SOC Console.
