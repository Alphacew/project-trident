"""Project TRIDENT — Enterprise Scenario Generator.

Implements generation for Scenarios A through E:
- Scenario A: Legitimate Role Change (High CAS, risk attenuated, Tier 1/2)
- Scenario B: Low-and-Slow Insider (Unanchored, cumulative CUSUM drift, Tier 3/4)
- Scenario C: Fabricated Context (Temporal mismatch, ghost ticket, low CAS, unsuppressed Tier 3/4)
- Scenario D: Emergency Incident (PagerDuty Sev-1, high CAS, attenuated Tier 1/2)
- Scenario E: Compromised Service Account (Non-human identity risk multiplier, rapid Tier 4)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
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
from backend.drift.cusum import CUSUMDriftEngine
from backend.drift.schemas import TrajectoryState
from backend.graph.schemas import EdgeType, NodeType
from backend.graph.subgraph_extractor import TimeWindowExtractor
from backend.graph.temporal_graph import TemporalGraphBuilder
from backend.risk.composite import CompositeRiskCalculator
from backend.risk.schemas import RiskTier
from backend.scenarios.schemas import (
    ScenarioDataset,
    ScenarioDaySnapshot,
    ScenarioExecutionResult,
    ScenarioMetadata,
    ScenarioType,
)
from backend.trust.anchor_engine import TrustAnchorEngine


class EnterpriseScenarioGenerator:
    """Generates synthetic enterprise datasets for Project TRIDENT evaluation."""

    def __init__(self, base_timestamp: Optional[datetime] = None):
        self.base_timestamp = base_timestamp or datetime(2026, 9, 1, 8, 0, 0, tzinfo=timezone.utc)

    # -------------------------------------------------------------------------
    # Helper to construct canonical events
    # -------------------------------------------------------------------------
    def _create_event(
        self,
        event_id: str,
        timestamp: datetime,
        actor_token: str,
        identity_type: IdentityType,
        action: str,
        resource_id: str,
        resource_type: str,
        sensitivity: float,
        event_type: EventType = EventType.DATA_ACCESS,
        ticket_ids: Optional[List[str]] = None,
        incident_ids: Optional[List[str]] = None,
        is_canary: bool = False,
        source_system: str = "okta",
    ) -> CanonicalEvent:
        return CanonicalEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            action=action,
            actor=ActorContext(
                actor_token=actor_token,
                identity_type=identity_type,
                role="Engineer",
                department="Engineering",
                peer_group="Backend-Core",
            ),
            resource=ResourceContext(
                resource_id=resource_id,
                resource_type=resource_type,
                sensitivity=sensitivity,
                is_canary=is_canary,
            ),
            network=NetworkContext(
                source_ip="10.0.1.50",
                destination_endpoint=resource_id,
                is_vpn=True,
            ),
            business_context=BusinessContext(
                ticket_ids=ticket_ids or [],
                incident_ids=incident_ids or [],
            ),
            raw_payload_hash=f"hash-{uuid.uuid4().hex[:12]}",
            source_system=source_system,
        )

    # -------------------------------------------------------------------------
    # SCENARIO A: Legitimate Role Change
    # -------------------------------------------------------------------------
    def generate_scenario_a_role_change(self) -> ScenarioDataset:
        """Scenario A: Developer promoted to Tech Lead.
        
        Accesses new repos and database with valid manager-approved Jira ticket.
        Expected: CAS >= 0.90, discount factor <= 0.25, composite risk <= Tier 2.
        """
        actor = "Subject-Alpha-101"
        historical = [
            "repo:corp/frontend-app",
            "repo:corp/backend-api",
            "repo:corp/shared-components",
            "repo:corp/docs",
        ]
        events: List[CanonicalEvent] = []
        anchors: List[AnchorCandidate] = []

        # Anchor: Promotion & Architecture Access ticket
        ticket_id = "JIRA-TECHLEAD-01"
        anchors.append(
            AnchorCandidate(
                anchor_id=ticket_id,
                anchor_type="JiraTicket",
                title="Promotion transition - Access to Architecture & Analytics DB",
                description="Promoted to Tech Lead. Granted read access to architecture specs and analytics warehouse.",
                created_at=(self.base_timestamp + timedelta(days=3)).replace(hour=10, minute=0),
                requester_id=actor,
                approver_id="mgr-director-eng",
                status="RESOLVED",
                is_emergency=False,
                target_resources=["repo:corp/architecture-specs", "db:analytics-warehouse"],
                downstream_artifacts=["PR-881", "PR-882", "COMMIT-9021"],
            )
        )

        # Days 1-3: Baseline work
        for day in range(1, 4):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, res in enumerate(historical):
                events.append(
                    self._create_event(
                        event_id=f"EVT-A-D{day}-{i}",
                        timestamp=day_t.replace(hour=10 + i, minute=0),
                        actor_token=actor,
                        identity_type=IdentityType.HUMAN,
                        action="git:clone",
                        resource_id=res,
                        resource_type="Repository",
                        sensitivity=0.25,
                        event_type=EventType.CODE_REPOSITORY,
                        source_system="github_audit",
                    )
                )

        # Days 4-7: Access new architecture repos and DB under valid ticket
        new_resources = [("repo:corp/architecture-specs", 0.40), ("db:analytics-warehouse", 0.60)]
        for day in range(4, 8):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, (res, sens) in enumerate(new_resources):
                events.append(
                    self._create_event(
                        event_id=f"EVT-A-D{day}-{i}",
                        timestamp=day_t.replace(hour=11 + (i * 2), minute=15),
                        actor_token=actor,
                        identity_type=IdentityType.HUMAN,
                        action="db:query" if "db:" in res else "git:pull",
                        resource_id=res,
                        resource_type="Database" if "db:" in res else "Repository",
                        sensitivity=sens,
                        event_type=EventType.DATABASE_QUERY if "db:" in res else EventType.CODE_REPOSITORY,
                        ticket_ids=[ticket_id],
                        source_system="aws_cloudtrail" if "db:" in res else "github_audit",
                    )
                )

        meta = ScenarioMetadata(
            scenario_id="SCENARIO_A",
            scenario_type=ScenarioType.SCENARIO_A_ROLE_CHANGE,
            name="Scenario A: Legitimate Role Change",
            description="Promotion to Tech Lead leading to new repos and analytics database access with valid Jira ticket.",
            primary_actor_token=actor,
            duration_days=7,
            expected_trajectory_state=TrajectoryState.STABLE,
            expected_risk_tier=RiskTier.TIER_1_CONTEXTUAL_DRIFT,
            key_signals=["Legitimate Context Attenuation", "High CAS (>0.85)", "Downstream Commits Corroboration"],
        )
        return ScenarioDataset(metadata=meta, events=events, anchors=anchors, historical_resources=historical)

    # -------------------------------------------------------------------------
    # SCENARIO B: Low-and-Slow Insider
    # -------------------------------------------------------------------------
    def generate_scenario_b_low_and_slow(self) -> ScenarioDataset:
        """Scenario B: 14 days of low-and-slow unanchored sensitive queries.
        
        Expected: CUSUM drift > 2.0, escalation to Tier 3 / Tier 4.
        """
        actor = "Subject-Theta-482"
        historical = [
            "repo:corp/frontend-app",
            "repo:corp/backend-api",
            "repo:corp/shared-components",
            "repo:corp/docs",
        ]
        events: List[CanonicalEvent] = []

        # Days 1-3: Baseline
        for day in range(1, 4):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, res in enumerate(historical):
                events.append(
                    self._create_event(
                        event_id=f"EVT-B-BASE-D{day}-{i}",
                        timestamp=day_t.replace(hour=10 + i, minute=10),
                        actor_token=actor,
                        identity_type=IdentityType.HUMAN,
                        action="git:clone",
                        resource_id=res,
                        resource_type="Repository",
                        sensitivity=0.25,
                        event_type=EventType.CODE_REPOSITORY,
                    )
                )

        # Days 4-14: Off-hours, slow sensitive DB/S3 queries with no ticket
        sensitive_targets = [
            ("db:customer-pii-shard-01", 0.85, "Database"),
            ("db:customer-pii-shard-02", 0.85, "Database"),
            ("db:eu-payroll-records", 0.95, "Database"),
            ("arn:aws:s3:::internal-financial-forecasts", 0.80, "Bucket"),
            ("arn:aws:s3:::corp-m-and-a-deal-docs", 0.90, "Bucket"),
            ("db:executive-compensation-ledger", 0.95, "Database"),
            ("arn:aws:s3:::cryptographic-keys-backup", 0.95, "Bucket"),
            ("db:customer-passwords-hashed", 0.95, "Database"),
            ("arn:aws:s3:::prod-customer-contracts", 0.85, "Bucket"),
            ("db:legal-dispute-settlements", 0.90, "Database"),
            ("bucket:corp-staging-mount", 0.85, "Bucket"),
        ]

        for day_idx, (target_res, sens, r_type) in enumerate(sensitive_targets, start=4):
            day_t = self.base_timestamp + timedelta(days=day_idx)
            for q in range(3):
                events.append(
                    self._create_event(
                        event_id=f"EVT-B-SLOW-D{day_idx}-{q}",
                        timestamp=day_t.replace(hour=19 + q, minute=20),
                        actor_token=actor,
                        identity_type=IdentityType.HUMAN,
                        action="SELECT * FROM table" if r_type == "Database" else "s3:GetObject",
                        resource_id=target_res,
                        resource_type=r_type,
                        sensitivity=sens,
                        event_type=EventType.DATABASE_QUERY if r_type == "Database" else EventType.DATA_ACCESS,
                        source_system="aws_cloudtrail",
                    )
                )

        meta = ScenarioMetadata(
            scenario_id="SCENARIO_B",
            scenario_type=ScenarioType.SCENARIO_B_LOW_AND_SLOW,
            name="Scenario B: Low-and-Slow Insider",
            description="Persistent, low-volume off-hours queries to sensitive databases and buckets over 14 days without ticket anchors.",
            primary_actor_token=actor,
            duration_days=14,
            expected_trajectory_state=TrajectoryState.CRITICAL,
            expected_risk_tier=RiskTier.TIER_4_CRITICAL,
            key_signals=["Cumulative Unanchored Drift", "CUSUM S_t Accumulation", "Cross-Boundary Entropy"],
        )
        return ScenarioDataset(metadata=meta, events=events, anchors=[], historical_resources=historical)

    # -------------------------------------------------------------------------
    # SCENARIO C: Fabricated Context
    # -------------------------------------------------------------------------
    def generate_scenario_c_fabricated_context(self) -> ScenarioDataset:
        """Scenario C: Suspicious access preceded 4 minutes by self-approved ticket.
        
        Expected: CAS <= 0.25 (temporal mismatch + approver conflict + ghost ticket).
        Risk fails suppression and remains in Tier 3 / Tier 4.
        """
        actor = "Subject-Gamma-771"
        historical = [
            "repo:corp/infra-terraform",
            "repo:corp/k8s-manifests",
            "repo:corp/observability-configs",
        ]
        events: List[CanonicalEvent] = []
        anchors: List[AnchorCandidate] = []

        day3_time = (self.base_timestamp + timedelta(days=3)).replace(hour=22, minute=8, second=0)
        ticket_time = day3_time - timedelta(minutes=4)  # 4 minutes before!

        # Fabricated Anchor
        ticket_id = "JIRA-841"
        anchors.append(
            AnchorCandidate(
                anchor_id=ticket_id,
                anchor_type="JiraTicket",
                title="Urgent DB Maintenance",
                description="Emergency schema patch on payroll records",
                created_at=ticket_time,
                requester_id=actor,
                approver_id=actor,  # Self-approved!
                status="OPEN",
                is_emergency=False,
                target_resources=["db:eu-payroll-records"],
                downstream_artifacts=[],  # Ghost ticket: no commits!
            )
        )

        # Days 1-2: Normal activity
        for day in range(1, 3):
            day_t = self.base_timestamp + timedelta(days=day)
            for i, res in enumerate(historical):
                events.append(
                    self._create_event(
                        event_id=f"EVT-C-D{day}-{i}",
                        timestamp=day_t.replace(hour=10 + i, minute=0),
                        actor_token=actor,
                        identity_type=IdentityType.HUMAN,
                        action="git:commit",
                        resource_id=res,
                        resource_type="Repository",
                        sensitivity=0.30,
                        event_type=EventType.CODE_REPOSITORY,
                    )
                )

        # Day 3: Fabricated Ticket access on highly sensitive EU Payroll DB
        events.append(
            self._create_event(
                event_id="EVT-C-D3-EXPLOIT",
                timestamp=day3_time,
                actor_token=actor,
                identity_type=IdentityType.HUMAN,
                action="SELECT * FROM eu_employees_salary_2026",
                resource_id="db:eu-payroll-records",
                resource_type="Database",
                sensitivity=0.95,
                event_type=EventType.DATABASE_QUERY,
                ticket_ids=[ticket_id],
                source_system="aws_cloudtrail",
            )
        )

        meta = ScenarioMetadata(
            scenario_id="SCENARIO_C",
            scenario_type=ScenarioType.SCENARIO_C_FABRICATED_CONTEXT,
            name="Scenario C: Fabricated Context",
            description="Off-hours extraction preceded 4 mins by self-approved ghost ticket. CAS drops; suppression denied.",
            primary_actor_token=actor,
            duration_days=3,
            expected_trajectory_state=TrajectoryState.UNANCHORED_EXPLORATION,
            expected_risk_tier=RiskTier.TIER_3_HIGH_RISK_TRAJECTORY,
            key_signals=["Temporal Mismatch (s1)", "Approver Conflict (s2)", "Ghost Ticket (s9)"],
        )
        return ScenarioDataset(metadata=meta, events=events, anchors=anchors, historical_resources=historical)

    # -------------------------------------------------------------------------
    # SCENARIO D: Emergency Incident
    # -------------------------------------------------------------------------
    def generate_scenario_d_emergency_incident(self) -> ScenarioDataset:
        """Scenario D: Deep off-hours Sev-1 incident response.
        
        Expected: Legitimate emergency anchor with high CAS attenuates risk to Tier 1/2.
        """
        actor = "Subject-Delta-302"
        historical = [
            "repo:corp/sre-tooling",
            "repo:corp/k8s-playbooks",
            "db:monitoring-telemetry",
        ]
        events: List[CanonicalEvent] = []
        anchors: List[AnchorCandidate] = []

        incident_time = (self.base_timestamp + timedelta(days=2)).replace(hour=2, minute=10, second=0)
        incident_id = "INC-991"

        anchors.append(
            AnchorCandidate(
                anchor_id=incident_id,
                anchor_type="PagerDutyIncident",
                title="Sev-1 Outage: Database deadlock on production customer database",
                description="Active production deadlock. On-call SRE paged for emergency intervention.",
                created_at=incident_time - timedelta(minutes=15),
                requester_id="pagerduty-system",
                approver_id="sre-commander-lead",
                status="OPEN",
                is_emergency=True,
                target_resources=["db:customer-core-prod"],
                downstream_artifacts=["SLACK-INC-CHANNEL", "RUNBOOK-EXEC-01"],
            )
        )

        # Day 1: Normal SRE tooling work
        day1_t = self.base_timestamp + timedelta(days=1)
        for i, res in enumerate(historical):
            events.append(
                self._create_event(
                    event_id=f"EVT-D-D1-{i}",
                    timestamp=day1_t.replace(hour=11 + i, minute=0),
                    actor_token=actor,
                    identity_type=IdentityType.HUMAN,
                    action="git:pull",
                    resource_id=res,
                    resource_type="Repository",
                    sensitivity=0.20,
                    event_type=EventType.CODE_REPOSITORY,
                )
            )

        # Day 2: 02:25 AM Emergency intervention on core database
        for q in range(3):
            events.append(
                self._create_event(
                    event_id=f"EVT-D-D2-INC-{q}",
                    timestamp=incident_time + timedelta(minutes=10 + (q * 5)),
                    actor_token=actor,
                    identity_type=IdentityType.HUMAN,
                    action="KILL SESSION / ALTER SYSTEM",
                    resource_id="db:customer-core-prod",
                    resource_type="Database",
                    sensitivity=0.85,
                    event_type=EventType.DATABASE_QUERY,
                    incident_ids=[incident_id],
                    source_system="aws_cloudtrail",
                )
            )

        meta = ScenarioMetadata(
            scenario_id="SCENARIO_D",
            scenario_type=ScenarioType.SCENARIO_D_EMERGENCY_INCIDENT,
            name="Scenario D: Emergency Incident",
            description="Deep off-hours intervention justified by critical PagerDuty incident. Risk attenuated.",
            primary_actor_token=actor,
            duration_days=2,
            expected_trajectory_state=TrajectoryState.STABLE,
            expected_risk_tier=RiskTier.TIER_1_CONTEXTUAL_DRIFT,
            key_signals=["Emergency Change Justification (s3)", "High CAS (>0.85)", "Attenuated Anomaly"],
        )
        return ScenarioDataset(metadata=meta, events=events, anchors=anchors, historical_resources=historical)

    # -------------------------------------------------------------------------
    # SCENARIO E: Compromised Service Account
    # -------------------------------------------------------------------------
    def generate_scenario_e_compromised_service_account(self) -> ScenarioDataset:
        """Scenario E: CI/CD runner exhibits unanchored privilege escalation and DB querying.
        
        Expected: Non-Human Identity risk multiplier (1.4x) accelerates rapid Tier 4 breach.
        """
        actor = "sa-github-deployer"
        historical = [
            "repo:corp/frontend-app",
            "repo:corp/backend-api",
            "bucket:build-artifacts",
        ]
        events: List[CanonicalEvent] = []

        # Day 1: Normal CI/CD pipeline builds
        day1_t = self.base_timestamp + timedelta(days=1)
        for i in range(4):
            events.append(
                self._create_event(
                    event_id=f"EVT-E-D1-{i}",
                    timestamp=day1_t.replace(hour=8 + (i * 2), minute=30),
                    actor_token=actor,
                    identity_type=IdentityType.CICD_RUNNER,
                    action="s3:PutObject",
                    resource_id="bucket:build-artifacts",
                    resource_type="Bucket",
                    sensitivity=0.30,
                    event_type=EventType.DATA_ACCESS,
                    source_system="aws_cloudtrail",
                )
            )

        # Day 2: Compromised token assumes admin role and dumps executive salaries
        day2_t = (self.base_timestamp + timedelta(days=2)).replace(hour=3, minute=15, second=0)
        events.append(
            self._create_event(
                event_id="EVT-E-D2-ROLE-ASSUME",
                timestamp=day2_t,
                actor_token=actor,
                identity_type=IdentityType.SERVICE_ACCOUNT,
                action="sts:AssumeRole (AdminEscalation)",
                resource_id="arn:aws:iam::role/ProductionAdmin",
                resource_type="Role",
                sensitivity=0.90,
                event_type=EventType.CLOUD_API,
                source_system="aws_cloudtrail",
            )
        )
        events.append(
            self._create_event(
                event_id="EVT-E-D2-QUERY-DB",
                timestamp=day2_t + timedelta(minutes=5),
                actor_token=actor,
                identity_type=IdentityType.SERVICE_ACCOUNT,
                action="SELECT * FROM executive_compensation_ledger",
                resource_id="db:executive-compensation-ledger",
                resource_type="Database",
                sensitivity=0.95,
                event_type=EventType.DATABASE_QUERY,
                source_system="aws_cloudtrail",
            )
        )

        meta = ScenarioMetadata(
            scenario_id="SCENARIO_E",
            scenario_type=ScenarioType.SCENARIO_E_COMPROMISED_SERVICE_ACCOUNT,
            name="Scenario E: Compromised Service Account",
            description="CI/CD runner token compromised; performs off-hours IAM role escalation and dumps executive compensation.",
            primary_actor_token=actor,
            duration_days=2,
            expected_trajectory_state=TrajectoryState.CRITICAL,
            expected_risk_tier=RiskTier.TIER_4_CRITICAL,
            key_signals=["Non-Human Identity Multiplier", "Privilege Expansion", "Unanchored Data Extraction"],
        )
        return ScenarioDataset(metadata=meta, events=events, anchors=[], historical_resources=historical)

    # -------------------------------------------------------------------------
    # End-to-End Scenario Runner
    # -------------------------------------------------------------------------
    def run_scenario(self, dataset: ScenarioDataset) -> ScenarioExecutionResult:
        """Executes a scenario dataset through the temporal graph and scoring engines."""
        builder = TemporalGraphBuilder()
        drift_engine = CUSUMDriftEngine()
        risk_calculator = CompositeRiskCalculator()
        anchor_engine = TrustAnchorEngine()

        actor_token = dataset.metadata.primary_actor_token
        drift_engine.reset_actor_state(actor_token)

        # Ingest all historical baseline resources
        hist_set = set(dataset.historical_resources)
        for res in dataset.historical_resources:
            builder.add_node(
                node_id=res,
                node_type=NodeType.REPOSITORY if "repo:" in res else NodeType.BUCKET,
                sensitivity=0.25,
                timestamp=self.base_timestamp,
            )

        # Convert candidate anchors into Trust ContextAnchors
        from backend.trust.schemas import AnchorType, ContextAnchor
        context_anchors: List[ContextAnchor] = []
        for anc in dataset.anchors:
            a_type = AnchorType.JIRA
            if "pagerduty" in anc.anchor_type.lower() or "inc" in anc.anchor_id.lower():
                a_type = AnchorType.PAGERDUTY
            elif "role" in anc.anchor_type.lower():
                a_type = AnchorType.HR_ROLE_CHANGE

            is_self = (anc.requester_id == anc.approver_id) if anc.approver_id else False
            dist = 0 if is_self else (1 if anc.approver_id and "director" not in anc.approver_id else 2)

            context_anchors.append(
                ContextAnchor(
                    anchor_id=anc.anchor_id,
                    anchor_type=a_type,
                    title=anc.title,
                    description=anc.description,
                    created_at=anc.created_at,
                    updated_at=anc.updated_at,
                    requester_id=anc.requester_id,
                    approver_id=anc.approver_id,
                    target_resources=anc.target_resources,
                    is_emergency=anc.is_emergency,
                    is_self_approved=is_self,
                    requester_approver_reporting_dist=dist,
                    downstream_commits_count=len(anc.downstream_artifacts),
                    downstream_prs_count=len([a for a in anc.downstream_artifacts if "PR" in a]),
                    corroborating_slack_messages_count=1 if anc.downstream_artifacts else 0,
                )
            )

        # Group events by chronological day
        snapshots: List[ScenarioDaySnapshot] = []
        extractor = TimeWindowExtractor(builder)

        for day in range(1, dataset.metadata.duration_days + 1):
            day_t = self.base_timestamp + timedelta(days=day)
            day_start = day_t.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_t.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Ingest events that belong to this day
            day_events = [
                e for e in dataset.events
                if day_start <= e.timestamp <= day_end
            ]
            for evt in day_events:
                builder.add_canonical_event(evt)

            # DevA extracts behavioral vector
            b_vec = extractor.extract_behavioral_vector(
                actor_token=actor_token,
                window_start=day_start,
                window_end=day_end,
                historical_resources=hist_set,
                expected_daily_volume=4.0,
            )

            # Trust Anchor Evaluation for day's events
            active_anchors = []
            for evt in day_events:
                claimed_ids = set(evt.business_context.ticket_ids + evt.business_context.incident_ids) if evt.business_context else set()
                matching_cands = [ca for ca in context_anchors if ca.anchor_id in claimed_ids] if claimed_ids else []
                if matching_cands:
                    res_eval = anchor_engine.evaluate(evt, candidate_anchors=matching_cands)
                    active_anchors.append(res_eval)

            if active_anchors:
                # Best anchor of the day
                best_eval = min(active_anchors, key=lambda a: a.discount_factor)
                discount_factor = best_eval.discount_factor
                cas_score = best_eval.anchor_score
            else:
                discount_factor = 1.0
                cas_score = 0.0

            # DevB CUSUM update
            drift_rep = drift_engine.update(
                actor_token=actor_token,
                current_vector=b_vec,
                discount_factor=discount_factor,
                timestamp=day_end,
            )

            # DevB Composite Risk
            # Raw anomaly tracks displacement from baseline
            raw_anomaly = min(1.0, max(0.05, drift_rep.displacement_raw / 1.5))
            identity_type = "ServiceAccount" if "sa-" in actor_token else "Human"

            risk_res = risk_calculator.evaluate(
                actor_token=actor_token,
                anomaly_score=raw_anomaly,
                anchor_score=cas_score,
                discount_factor=discount_factor,
                cumulative_drift_score=drift_rep.normalized_drift_score,
                resource_criticality=b_vec.resource_sensitivity_mean or 0.25,
                identity_type=identity_type,
                timestamp=day_end,
            )

            # Check canary status
            canary_active = any(
                builder.get_node(e.target_id) and builder.get_node(e.target_id).is_canary
                for e in [builder.get_edge(eid) for eid in builder.get_edge_ids_in_window(day_start, day_end)]
                if e
            )
            canary_state = "CONFIRMED" if canary_active else ("PREDICTED" if day >= 12 and dataset.metadata.scenario_id == "MASTER_DEMO" else "UNCONFIRMED")

            snapshot = ScenarioDaySnapshot(
                day=day,
                timestamp=day_end,
                events_count=len(day_events),
                raw_anomaly_score=round(raw_anomaly, 4),
                context_authenticity_score=round(cas_score, 4),
                discount_factor=round(discount_factor, 4),
                attenuated_anomaly_score=round(raw_anomaly * discount_factor, 4),
                cusum_drift_score=round(drift_rep.cusum_drift_score, 4),
                drift_velocity=round(drift_rep.drift_velocity, 4),
                trajectory_state=drift_rep.trajectory_state,
                composite_risk=risk_res.composite_risk,
                risk_tier=risk_res.risk_tier,
                canary_state=canary_state,
                active_mitre_tactics=risk_res.mitre_tactics,
            )
            snapshots.append(snapshot)

        final_snap = snapshots[-1]
        passed = (
            final_snap.risk_tier == dataset.metadata.expected_risk_tier
            or (dataset.metadata.expected_risk_tier in [RiskTier.TIER_3_HIGH_RISK_TRAJECTORY, RiskTier.TIER_4_CRITICAL]
                and final_snap.risk_tier in [RiskTier.TIER_3_HIGH_RISK_TRAJECTORY, RiskTier.TIER_4_CRITICAL])
        )

        return ScenarioExecutionResult(
            metadata=dataset.metadata,
            daily_snapshots=snapshots,
            final_drift_score=final_snap.cusum_drift_score,
            final_trajectory_state=final_snap.trajectory_state,
            final_risk_score=final_snap.composite_risk,
            final_risk_tier=final_snap.risk_tier,
            evaluation_passed=passed,
            evaluation_notes=f"Completed {len(snapshots)} days. Final tier: {final_snap.risk_tier.value}",
        )
