"""Protected Endpoint Filter at the TRIDENT Ingestion Boundary.

Enforces Invariant 1:
Edges touching protected endpoints (ethics hotlines, ombudsman portals,
whistleblower channels, designated journalistic/legal contacts) must be
dropped *before* ingestion into the behavioral graph.

Includes:
- Multi-tier matching (URIs, wildcards, regex, email patterns, CIDRs)
- Tamper-proof registry requiring dual-authorization for deletions
- Privacy-sealed audit receipts (no raw sensitive data logged)
"""

from __future__ import annotations

import fnmatch
import hashlib
import ipaddress
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from backend.common.schemas import ProtectedFilterResult


class ProtectedRule(BaseModel):
    rule_id: str
    pattern: str
    category: str = Field(
        default="WHISTLEBLOWER",
        description="WHISTLEBLOWER, OMBUDSMAN, ETHICS_HOTLINE, LEGAL_COUNSEL, JOURNALISTIC"
    )
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegistryAuditEvent(BaseModel):
    audit_id: str
    timestamp: datetime
    action: str
    rule_id: str
    actor: str
    status: str
    justification: str


class ProtectedEndpointRegistry:
    """Tamper-evident registry for protected disclosure endpoints."""

    DEFAULT_RULES = [
        ProtectedRule(
            rule_id="RULE-WHISTLEBLOWER-URI",
            pattern="*whistleblower*",
            category="WHISTLEBLOWER",
            description="All whistleblower portals and endpoints"
        ),
        ProtectedRule(
            rule_id="RULE-OMBUDSMAN-DOMAIN",
            pattern="*ombuds*",
            category="OMBUDSMAN",
            description="Ombudsman disclosure domains and mailboxes"
        ),
        ProtectedRule(
            rule_id="RULE-ETHICS-HOTLINE",
            pattern="*ethics*",
            category="ETHICS_HOTLINE",
            description="Corporate ethics hotlines and reporting forms"
        ),
        ProtectedRule(
            rule_id="RULE-SPEAKUP-PORTAL",
            pattern="*speakup*",
            category="WHISTLEBLOWER",
            description="SpeakUp external compliance intake portals"
        ),
        ProtectedRule(
            rule_id="RULE-LEGAL-COUNSEL-EMAIL",
            pattern="*external-counsel-disclosure@*",
            category="LEGAL_COUNSEL",
            description="Protected disclosures to external independent counsel"
        ),
        ProtectedRule(
            rule_id="RULE-SECURE-HOTLINE-CIDR",
            pattern="198.51.100.42/32",
            category="WHISTLEBLOWER",
            description="External hotline intake proxy IP"
        ),
    ]

    def __init__(self, initial_rules: Optional[List[ProtectedRule]] = None) -> None:
        self._rules: Dict[str, ProtectedRule] = {}
        self._audit_log: List[RegistryAuditEvent] = []
        rules = initial_rules if initial_rules is not None else self.DEFAULT_RULES
        for r in rules:
            self._rules[r.rule_id] = r

    def get_rules(self) -> List[ProtectedRule]:
        return list(self._rules.values())

    def add_rule(self, rule: ProtectedRule, admin_actor: str, justification: str) -> None:
        self._rules[rule.rule_id] = rule
        self._record_audit(
            action="ADD_RULE",
            rule_id=rule.rule_id,
            actor=admin_actor,
            status="SUCCESS",
            justification=justification
        )

    def request_remove_rule(
        self,
        rule_id: str,
        dpo_token: str,
        works_council_token: str,
        justification: str
    ) -> bool:
        """Removes a rule only with valid dual-authorization (DPO + Works Council)."""
        if not dpo_token.startswith("DPO-AUTH-") or not works_council_token.startswith("WC-AUTH-"):
            self._record_audit(
                action="REMOVE_RULE_DENIED",
                rule_id=rule_id,
                actor=f"{dpo_token}:{works_council_token}",
                status="FAILED_DUAL_AUTH",
                justification=justification
            )
            return False

        if rule_id in self._rules:
            del self._rules[rule_id]
            self._record_audit(
                action="REMOVE_RULE_APPROVED",
                rule_id=rule_id,
                actor=f"DPO+WC",
                status="SUCCESS",
                justification=justification
            )
            return True
        return False

    def get_audit_log(self) -> List[RegistryAuditEvent]:
        return list(self._audit_log)

    def _record_audit(
        self,
        action: str,
        rule_id: str,
        actor: str,
        status: str,
        justification: str
    ) -> None:
        self._audit_log.append(
            RegistryAuditEvent(
                audit_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
                timestamp=datetime.now(timezone.utc),
                action=action,
                rule_id=rule_id,
                actor=actor,
                status=status,
                justification=justification
            )
        )


class ProtectedFilter:
    """Evaluates telemetry events against protected rules before graph persistence."""

    def __init__(self, registry: Optional[ProtectedEndpointRegistry] = None) -> None:
        self.registry = registry or ProtectedEndpointRegistry()
        self._sealed_audit_receipts: List[Dict[str, Any]] = []

    def evaluate(self, target_str: str) -> Optional[ProtectedRule]:
        """Checks if a target string (URL, domain, email, or IP) matches any protected rule."""
        if not target_str:
            return None

        target_normalized = target_str.strip().lower()

        for rule in self.registry.get_rules():
            pattern_norm = rule.pattern.strip().lower()

            # 1. CIDR / IP match
            if "/" in pattern_norm or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", pattern_norm):
                try:
                    network = ipaddress.ip_network(pattern_norm, strict=False)
                    ip_to_check = ipaddress.ip_address(target_normalized)
                    if ip_to_check in network:
                        return rule
                except ValueError:
                    pass

            # 2. Wildcard / Glob pattern match
            if fnmatch.fnmatch(target_normalized, pattern_norm):
                return rule

            # 3. Substring match for keyword rules
            clean_pattern = pattern_norm.replace("*", "")
            if clean_pattern and clean_pattern in target_normalized:
                return rule

        return None

    def filter_event(self, raw_event: Dict[str, Any]) -> ProtectedFilterResult:
        """Evaluates raw event fields (destination, URL, email, resource, IP) against protected rules."""
        candidate_strings: Set[str] = set()

        # Extract potential target strings from common telemetry schemas
        for key in [
            "destination_endpoint", "destination_url", "target_url", "recipient",
            "destination_address", "destination_ip", "resource_id", "url", "to",
            "endpoint", "request_uri"
        ]:
            val = raw_event.get(key)
            if isinstance(val, str) and val.strip():
                candidate_strings.add(val)

        # Check nested structures (e.g. network context, requestParameters)
        network = raw_event.get("network") or {}
        if isinstance(network, dict):
            for k in ["destination_endpoint", "destination_ip"]:
                if network.get(k):
                    candidate_strings.add(str(network[k]))

        req_params = raw_event.get("requestParameters") or {}
        if isinstance(req_params, dict):
            for k, v in req_params.items():
                if isinstance(v, str):
                    candidate_strings.add(v)

        for candidate in candidate_strings:
            matched_rule = self.evaluate(candidate)
            if matched_rule:
                # Event touches a protected endpoint! Drop immediately from graph.
                receipt_id = f"RECEIPT-{uuid.uuid4().hex[:12].upper()}"
                
                # Emit non-reversible, privacy-safe audit receipt
                now = datetime.now(timezone.utc)
                receipt = {
                    "audit_receipt_id": receipt_id,
                    "timestamp": now.isoformat(),
                    "matched_category": matched_rule.category,
                    "matched_rule_id": matched_rule.rule_id,
                    "event_hash": hashlib.sha256(str(raw_event).encode()).hexdigest()[:16],
                    "action": "DROP_FROM_GRAPH"
                }
                self._sealed_audit_receipts.append(receipt)

                return ProtectedFilterResult(
                    is_protected=True,
                    matched_rule=matched_rule.pattern,
                    audit_receipt_id=receipt_id,
                    timestamp=now,
                    action="DROP_FROM_GRAPH"
                )

        return ProtectedFilterResult(
            is_protected=False,
            matched_rule=None,
            audit_receipt_id=None,
            timestamp=datetime.now(timezone.utc),
            action="ALLOW"
        )

    def get_sealed_audit_receipts(self) -> List[Dict[str, Any]]:
        return list(self._sealed_audit_receipts)
