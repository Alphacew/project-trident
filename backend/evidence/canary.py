"""Project TRIDENT — Simulated Canary & Deception Engine.

Manages simulated decoy canary resources, predicted threat targeting,
and transitions through evidence confirmation states:
UNCONFIRMED -> PREDICTED -> CONFIRMED

Invariant: Explicitly labeled as 'Simulated Canary' per Claim Ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.evidence.schemas import CanaryDecoy, EvidenceConfirmationState


class SimulatedCanaryEngine:
    """Manages active canary decoys and deception state machine."""

    def __init__(self):
        self._canaries: Dict[str, CanaryDecoy] = {}
        self._init_default_decoys()

    def _init_default_decoys(self):
        """Initializes canonical simulated canary decoys."""
        now = datetime.now(timezone.utc)
        default_decoys = [
            CanaryDecoy(
                canary_id="CANARY-S3-PAYROLL",
                resource_id="arn:aws:s3:::canary-decoy-payroll-backup",
                resource_type="Bucket",
                created_at=now,
                is_tripped=False,
                claim_label="Simulated Canary",
            ),
            CanaryDecoy(
                canary_id="CANARY-DB-SALARY",
                resource_id="db:decoy-executive-salaries",
                resource_type="Database",
                created_at=now,
                is_tripped=False,
                claim_label="Simulated Canary",
            ),
        ]
        for c in default_decoys:
            self._canaries[c.resource_id] = c

    def get_canary(self, resource_id: str) -> Optional[CanaryDecoy]:
        return self._canaries.get(resource_id)

    def get_all_canaries(self) -> List[CanaryDecoy]:
        return list(self._canaries.values())

    def predict_target(self, actor_token: str, resource_id: str) -> Optional[CanaryDecoy]:
        """Sets predicted target asset for an escalating actor."""
        canary = self._canaries.get(resource_id)
        if canary:
            canary.predicted_threat_actor = actor_token
            if not canary.is_tripped:
                canary.confirmation_state = EvidenceConfirmationState.PREDICTED
        return canary

    def trigger_trip(
        self,
        resource_id: str,
        actor_token: str,
        timestamp: Optional[datetime] = None,
    ) -> CanaryDecoy:
        """Triggers a canary trip, advancing confirmation state to CONFIRMED."""
        canary = self._canaries.get(resource_id)
        now = timestamp or datetime.now(timezone.utc)
        if not canary:
            canary = CanaryDecoy(
                canary_id=f"CANARY-{resource_id.split(':')[-1][:12].upper()}",
                resource_id=resource_id,
                resource_type="Bucket",
                created_at=now,
                is_tripped=True,
                trip_timestamp=now,
                tripped_by_actor=actor_token,
                confirmation_state=EvidenceConfirmationState.CONFIRMED,
                claim_label="Simulated Canary",
            )
            self._canaries[resource_id] = canary
        else:
            canary.is_tripped = True
            canary.trip_timestamp = now
            canary.tripped_by_actor = actor_token
            canary.confirmation_state = EvidenceConfirmationState.CONFIRMED

        return canary

    def get_primary_status(self) -> CanaryDecoy:
        """Returns the primary demo canary status."""
        primary_id = "arn:aws:s3:::canary-decoy-payroll-backup"
        return self._canaries.get(primary_id, list(self._canaries.values())[0])
