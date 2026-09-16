"""Project TRIDENT — FastAPI Backend Application.

Initializes FastAPI app with CORS middleware and registers modular routes:
- /api/timeline (Screen 1 Dual Timeline)
- /api/graph (Screen 2 React Flow Causal Graph)
- /api/risk (Risk Trajectory & Drift)
- /api/canary (Simulated Canary Deception)
- /api/scenarios (Enterprise Scenario Runner)
- /api/evidence (Forensic Dossier & MITRE ATT&CK)
- /api/privacy (Screen 3 Shamir Vault & Dual Custody)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import (
    canary,
    evidence,
    graph,
    privacy,
    risk,
    scenarios,
    timeline,
)

app = FastAPI(
    title="Project TRIDENT API",
    description="Trust-Anchored Risk Intelligence, Drift & Evidence Network REST API",
    version="1.0.0",
)

# Enable CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(timeline.router)
app.include_router(graph.router)
app.include_router(risk.router)
app.include_router(canary.router)
app.include_router(scenarios.router)
app.include_router(evidence.router)
app.include_router(privacy.router)


@app.get("/")
def root():
    return {
        "service": "Project TRIDENT API",
        "tagline": "Trust the context. Track the trajectory. Prove the threat.",
        "version": "1.0.0",
        "status": "operational",
        "claim_label": "Measured Today",
    }
