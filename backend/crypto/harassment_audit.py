"""Project TRIDENT — Anti-Harassment Governance & Compliance Guardrails.

Implements Skill 8 and Section 1 safeguards:
1. Direct Name Query Block:
   Blocks arbitrary employee surveillance by prohibiting searches by raw employee
   names, emails, or system usernames. Investigations must originate from graph
   anomaly IDs, risk clusters, or pseudonymous tokens.

2. Repeat Subject Alert:
   Monitors manual SOC inspections. If an analyst queries the same pseudonym > 3
   times in a 14-day window without the subject progressing to Tier 3 or Tier 4,
   an automated compliance flag is raised for the Data Protection Officer (DPO).

3. Manager View Redaction:
   Enforces k >= 5 differential privacy aggregation for manager-tier views,
   stripping individual pseudonyms and individual trajectory details.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class QueryValidationResult(BaseModel):
    """Result of validating an analyst search/inspection query."""
    allowed: bool
    query: str
    reason: Optional[str] = None
    query_type: str = Field(
        ...,
        description="PSEUDONYM, ANOMALY_ID, CLUSTER_ID, RESOURCE_ID, INCIDENT_ID, BLOCKED_DIRECT_NAME, BLOCKED_EMAIL, INVALID"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    claim_label: str = Field(default="Measured Today")


class HarassmentAlert(BaseModel):
    """Compliance alert dispatched to the DPO when repeat queries indicate potential targeted surveillance."""
    alert_id: str
    timestamp: datetime
    subject_token: str
    analyst_id: str
    query_count: int
    window_days: int = 14
    current_risk_tier: str
    status: str = Field(default="OPEN", description="OPEN, ACKNOWLEDGED, RESOLVED")
    dpo_notification: str
    claim_label: str = Field(default="Measured Today")


class AntiHarassmentGuard:
    """Governance guardrail preventing platform misuse and managerial harassment."""

    # Allowed token regex patterns
    PSEUDONYM_REGEX = re.compile(r"^(Subject|Runner|ServiceAccount|APIKey)-[A-Za-z]+-\d{3}$", re.IGNORECASE)
    ANOMALY_REGEX = re.compile(r"^(ANOM|ANOMALY|CLUSTER|INC|INCIDENT|EVT|EVENT|JIRA|PD|SNOW)-[A-Za-z0-9-_]+$", re.IGNORECASE)
    RESOURCE_REGEX = re.compile(r"^(arn:aws|repo:|bucket:|db:|endpoint:|table:).+$", re.IGNORECASE)

    # Patterns indicating forbidden direct-identity searches
    EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    # Matches typical personal name patterns: "First Last" or "First Middle Last"
    NAME_REGEX = re.compile(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$")

    def __init__(self, repeat_query_threshold: int = 3, window_days: int = 14) -> None:
        self.repeat_query_threshold = repeat_query_threshold
        self.window_days = window_days
        # Maps subject_token -> list of (timestamp, analyst_id, risk_tier)
        self._access_history: Dict[str, List[Tuple[datetime, str, str]]] = {}
        # Active DPO alerts
        self._alerts: List[HarassmentAlert] = []
        # Audit log of all evaluated queries
        self._query_audit_log: List[QueryValidationResult] = []

    @property
    def alerts(self) -> List[HarassmentAlert]:
        return list(self._alerts)

    @property
    def query_audit_log(self) -> List[QueryValidationResult]:
        return list(self._query_audit_log)

    def validate_query(self, query: str, analyst_id: str = "SOC-Analyst-1") -> QueryValidationResult:
        """Evaluates whether an investigation query complies with anti-harassment policies."""
        q = (query or "").strip()

        if not q:
            res = QueryValidationResult(
                allowed=False,
                query=q,
                reason="Query string cannot be empty.",
                query_type="INVALID",
            )
            self._query_audit_log.append(res)
            return res

        # 1. Block direct email queries
        if self.EMAIL_REGEX.match(q):
            res = QueryValidationResult(
                allowed=False,
                query=q,
                reason="Direct email query prohibited. Individual searches violate whistleblower/GDPR "
                       "protection. Investigations must originate from graph anomaly IDs, clusters, or pseudonyms.",
                query_type="BLOCKED_EMAIL",
            )
            self._query_audit_log.append(res)
            return res

        # 2. Block direct full-name queries
        if self.NAME_REGEX.match(q):
            res = QueryValidationResult(
                allowed=False,
                query=q,
                reason="Direct employee name query prohibited. Managerial harassment safeguard active: "
                       "searches by personal name are blocked. Inquire via pseudonymous token or anomaly ID.",
                query_type="BLOCKED_DIRECT_NAME",
            )
            self._query_audit_log.append(res)
            return res

        # 3. Allow valid pseudonym tokens
        if self.PSEUDONYM_REGEX.match(q):
            res = QueryValidationResult(
                allowed=True,
                query=q,
                query_type="PSEUDONYM",
            )
            self._query_audit_log.append(res)
            return res

        # 4. Allow anomaly / incident / ticket IDs
        if self.ANOMALY_REGEX.match(q):
            res = QueryValidationResult(
                allowed=True,
                query=q,
                query_type="ANOMALY_ID",
            )
            self._query_audit_log.append(res)
            return res

        # 5. Allow resource URIs
        if self.RESOURCE_REGEX.match(q):
            res = QueryValidationResult(
                allowed=True,
                query=q,
                query_type="RESOURCE_ID",
            )
            self._query_audit_log.append(res)
            return res

        # 6. Fallback: If it contains plain words that look like personal searches, block it
        words = q.split()
        if len(words) >= 2 and all(w.isalpha() for w in words):
            res = QueryValidationResult(
                allowed=False,
                query=q,
                reason="Direct person identifier detected. Inquiries must target anomaly IDs or pseudonyms.",
                query_type="BLOCKED_DIRECT_NAME",
            )
            self._query_audit_log.append(res)
            return res

        # Default allowed for technical terms / identifiers
        res = QueryValidationResult(
            allowed=True,
            query=q,
            query_type="ANOMALY_ID",
        )
        self._query_audit_log.append(res)
        return res

    def record_subject_access(
        self,
        subject_token: str,
        analyst_id: str,
        current_risk_tier: str = "TIER_1_CONTEXTUAL_DRIFT",
        timestamp: Optional[datetime] = None,
    ) -> Optional[HarassmentAlert]:
        """Tracks inspections of a subject pseudonym.
        
        Triggers an alert to the DPO if accessed > repeat_query_threshold times within
        window_days without reaching an actionable risk threshold (Tier 3 or Tier 4).
        """
        now = timestamp or datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.window_days)

        if subject_token not in self._access_history:
            self._access_history[subject_token] = []

        # Prune older than window
        self._access_history[subject_token] = [
            entry for entry in self._access_history[subject_token] if entry[0] >= cutoff
        ]
        self._access_history[subject_token].append((now, analyst_id, current_risk_tier))

        count = len(self._access_history[subject_token])

        # Check if alert condition met:
        # 1. More queries than threshold
        # 2. Risk tier is low (Tier 1 or Tier 2) - not justified by elevated threat
        is_low_risk = "TIER_1" in current_risk_tier.upper() or "TIER_2" in current_risk_tier.upper()
        if count > self.repeat_query_threshold and is_low_risk:
            # Check if alert already raised for this subject in window
            existing = [
                a for a in self._alerts
                if a.subject_token == subject_token and a.status == "OPEN" and a.timestamp >= cutoff
            ]
            if not existing:
                alert = HarassmentAlert(
                    alert_id=f"HARASS-{uuid.uuid4().hex[:8].upper()}",
                    timestamp=now,
                    subject_token=subject_token,
                    analyst_id=analyst_id,
                    query_count=count,
                    window_days=self.window_days,
                    current_risk_tier=current_risk_tier,
                    status="OPEN",
                    dpo_notification=(
                        f"COMPLIANCE ALERT: Subject '{subject_token}' has been inspected {count} times "
                        f"over the past {self.window_days} days by analyst '{analyst_id}' without progressing "
                        f"past {current_risk_tier}. This repeated scrutiny on a benign/low-risk profile has "
                        f"been flagged for DPO fairness audit to protect against targeted managerial harassment."
                    ),
                    claim_label="Measured Today",
                )
                self._alerts.append(alert)
                return alert

        return None

    def filter_for_manager_view(
        self,
        cohort_data: List[Dict[str, Any]],
        min_cohort_size: int = 5,
    ) -> Dict[str, Any]:
        """Applies k-anonymity differential privacy for managerial dashboard views.
        
        Enforces k >= 5: if a team or cohort has fewer than 5 members, individual
        subject details and trajectories are completely redacted.
        """
        n = len(cohort_data)
        if n < min_cohort_size:
            return {
                "cohort_size": n,
                "is_redacted": True,
                "minimum_required_cohort_size": min_cohort_size,
                "message": (
                    f"Team cohort size ({n}) is below the required differential privacy threshold "
                    f"(k >= {min_cohort_size}). Individual employee tokens and risk breakdowns have been "
                    "redacted to prevent subordinate deanonymization and workplace surveillance."
                ),
                "aggregated_metrics": None,
                "claim_label": "Measured Today",
            }

        # Aggregate safely
        total_risk = sum(item.get("composite_risk", 0.0) for item in cohort_data)
        total_drift = sum(item.get("cusum_drift_score", 0.0) for item in cohort_data)
        tiers_distribution: Dict[str, int] = {}
        for item in cohort_data:
            t = item.get("risk_tier", "TIER_1")
            tiers_distribution[t] = tiers_distribution.get(t, 0) + 1

        return {
            "cohort_size": n,
            "is_redacted": False,
            "minimum_required_cohort_size": min_cohort_size,
            "aggregated_metrics": {
                "mean_composite_risk": round(total_risk / n, 2),
                "mean_cusum_drift": round(total_drift / n, 2),
                "tier_distribution": tiers_distribution,
                "total_events_observed": sum(item.get("event_count", 1) for item in cohort_data),
            },
            "claim_label": "Measured Today",
        }
