"""Skill 1: OCSF Event Normalizer & Pre-Graph Ingestion Pipeline.

Parses incoming raw telemetry (Okta, CloudTrail, GitHub, Jira, ServiceNow, PagerDuty)
into OCSF-compliant CanonicalEvent records, enforces the Protected Endpoint Filter,
and applies HMAC-SHA-256 pseudonymization to actor identities.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.common.schemas import (
    ActorContext,
    BusinessContext,
    CanonicalEvent,
    EventType,
    IdentityType,
    NetworkContext,
    ProtectedFilterResult,
    ResourceContext,
)
from backend.ingestion.protected_filter import ProtectedEndpointRegistry, ProtectedFilter
from backend.ingestion.pseudonymizer import HMACIdentityPseudonymizer


class OCSFEventNormalizer:
    """Ingestion pipeline normalizer enforcing privacy invariants before graph construction."""

    def __init__(
        self,
        protected_registry: Optional[ProtectedEndpointRegistry] = None,
        pseudonymizer: Optional[HMACIdentityPseudonymizer] = None,
        salt_key: Optional[bytes] = None,
    ) -> None:
        self.protected_filter = ProtectedFilter(registry=protected_registry)
        self.pseudonymizer = pseudonymizer or HMACIdentityPseudonymizer(hmac_salt=salt_key)

    def normalize_event(
        self,
        raw_event: Union[Dict[str, Any], str]
    ) -> Tuple[Optional[CanonicalEvent], ProtectedFilterResult]:
        """Core procedural normalization pipeline.
        
        Returns:
            Tuple of (CanonicalEvent or None if dropped, ProtectedFilterResult)
        """
        # 0. Parse JSON if string provided
        if isinstance(raw_event, str):
            try:
                payload = json.loads(raw_event)
            except Exception:
                payload = {"raw_text": raw_event}
        else:
            payload = dict(raw_event)

        # 1. Inspect protected endpoints BEFORE any graph object is formed (Invariant 1)
        filter_res = self.protected_filter.filter_event(payload)
        if filter_res.is_protected:
            # Drop from graph and return None
            return None, filter_res

        # 2. Extract and parse source telemetry
        source_system = self._detect_source_system(payload)
        raw_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

        # 3. Parse components according to source system
        event_id = str(payload.get("event_id") or payload.get("eventId") or f"EVT-{uuid.uuid4().hex[:12].upper()}")
        ts = self._parse_timestamp(payload)
        event_type, action = self._parse_event_action(payload, source_system)
        actor = self._parse_actor(payload, source_system)
        resource = self._parse_resource(payload, source_system)
        network = self._parse_network(payload)
        biz_context = self._parse_business_context(payload)

        # 4. Construct immutable CanonicalEvent (Invariant 6: raw_id is never persisted in graph)
        canonical = CanonicalEvent(
            event_id=event_id,
            timestamp=ts,
            event_type=event_type,
            action=action,
            actor=actor,
            resource=resource,
            network=network,
            business_context=biz_context,
            raw_payload_hash=raw_hash,
            source_system=source_system,
            attributes=payload.get("attributes", {})
        )

        return canonical, filter_res

    def _detect_source_system(self, payload: Dict[str, Any]) -> str:
        if "eventSource" in payload and any(s in str(payload.get("eventSource")).lower() for s in ["cloudtrail", "amazonaws.com"]):
            return "aws_cloudtrail"
        if "userIdentity" in payload or "awsRegion" in payload:
            return "aws_cloudtrail"
        if "eventType" in payload and any(k in payload for k in ["actor", "client", "target"]):
            return "okta"
        if "repository" in payload or "org" in payload:
            return "github_audit"
        if "issue" in payload or "ticket_id" in payload or "jira" in str(payload).lower():
            return "jira"
        if "incident" in payload or "pagerduty" in str(payload).lower():
            return "pagerduty"
        return payload.get("source_system", "generic")

    def _parse_timestamp(self, payload: Dict[str, Any]) -> datetime:
        for k in ["timestamp", "eventTime", "published", "created_at", "time"]:
            val = payload.get(k)
            if val:
                if isinstance(val, datetime):
                    return val
                try:
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                except ValueError:
                    pass
        return datetime.now(timezone.utc)

    def _parse_event_action(self, payload: Dict[str, Any], source: str) -> Tuple[EventType, str]:
        if source == "aws_cloudtrail":
            action = payload.get("eventName", "cloudtrail:action")
            ev_type = EventType.CLOUD_API
            if "s3" in action.lower() or "getobject" in action.lower():
                ev_type = EventType.DATA_ACCESS
            elif "assumerole" in action.lower():
                ev_type = EventType.AUTHORIZATION
            return ev_type, action

        if source == "okta":
            action = payload.get("eventType", "okta:session.start")
            return EventType.AUTHENTICATION, action

        if source == "github_audit":
            action = payload.get("action", "git:clone")
            return EventType.CODE_REPOSITORY, action

        if source == "jira":
            action = payload.get("action", "ticket:update")
            return EventType.TICKET, action

        if source == "pagerduty":
            action = payload.get("action", "incident:trigger")
            return EventType.INCIDENT, action

        # Fallback generic
        action = str(payload.get("action") or "system:operation")
        ev_type = EventType.SYSTEM
        if "query" in action.lower() or "select" in action.lower():
            ev_type = EventType.DATABASE_QUERY
        elif "stage" in action.lower() or "copy" in action.lower():
            ev_type = EventType.DATA_STAGING
        elif "exfil" in action.lower() or "upload" in action.lower():
            ev_type = EventType.DATA_EXFILTRATION

        return ev_type, action

    def _parse_actor(self, payload: Dict[str, Any], source: str) -> ActorContext:
        raw_id = "unknown_actor"
        identity_type = IdentityType.HUMAN
        role = None
        dept = None

        if source == "aws_cloudtrail":
            userIdentity = payload.get("userIdentity") or {}
            raw_id = userIdentity.get("arn") or userIdentity.get("userName") or "aws_actor"
            type_str = str(userIdentity.get("type", "")).lower()
            if "assumedrole" in type_str or "service" in type_str:
                identity_type = IdentityType.SERVICE_ACCOUNT
            elif "runner" in raw_id.lower() or "cicd" in raw_id.lower():
                identity_type = IdentityType.CICD_RUNNER

        elif source == "okta":
            actor = payload.get("actor") or {}
            raw_id = actor.get("alternateId") or actor.get("id") or "okta_user"
            role = payload.get("role")
            dept = payload.get("department")

        else:
            raw_id = str(
                payload.get("actor_id") or
                payload.get("user_id") or
                payload.get("actor") or
                payload.get("user") or
                "unknown_entity"
            )
            type_str = str(payload.get("identity_type", "")).lower()
            if "service" in type_str:
                identity_type = IdentityType.SERVICE_ACCOUNT
            elif "runner" in type_str or "cicd" in type_str:
                identity_type = IdentityType.CICD_RUNNER

        # Ingestion Pseudonymization (Invariant 6)
        actor_token = self.pseudonymizer.pseudonymize(raw_id, identity_type=identity_type)

        return ActorContext(
            actor_token=actor_token,
            identity_type=identity_type,
            raw_id=None,  # NEVER leak raw_id onto the graph representation
            role=role,
            department=dept,
            peer_group=payload.get("peer_group")
        )

    def _parse_resource(self, payload: Dict[str, Any], source: str) -> ResourceContext:
        res_id = str(
            payload.get("resource_id") or
            payload.get("resource") or
            payload.get("target") or
            "generic-resource-id"
        )
        res_type = str(payload.get("resource_type") or "GenericResource")
        sensitivity = float(payload.get("sensitivity", 0.5))
        is_canary = bool(payload.get("is_canary", False) or "canary" in res_id.lower())

        if source == "aws_cloudtrail":
            resources = payload.get("resources") or []
            if resources and isinstance(resources, list) and isinstance(resources[0], dict):
                res_id = resources[0].get("ARN") or res_id
                res_type = resources[0].get("type") or "AWSResource"

        return ResourceContext(
            resource_id=res_id,
            resource_type=res_type,
            sensitivity=sensitivity,
            department_owner=payload.get("department_owner"),
            is_canary=is_canary
        )

    def _parse_network(self, payload: Dict[str, Any]) -> NetworkContext:
        net = payload.get("network") or {}
        return NetworkContext(
            source_ip=payload.get("sourceIPAddress") or net.get("source_ip"),
            destination_endpoint=payload.get("destination_endpoint") or net.get("destination_endpoint"),
            destination_ip=payload.get("destination_ip") or net.get("destination_ip"),
            user_agent=payload.get("userAgent") or net.get("user_agent"),
            is_vpn=net.get("is_vpn")
        )

    def _parse_business_context(self, payload: Dict[str, Any]) -> BusinessContext:
        biz = payload.get("business_context") or {}
        ticket_ids = biz.get("ticket_ids") or []
        if "ticket_id" in payload and payload["ticket_id"] not in ticket_ids:
            ticket_ids.append(payload["ticket_id"])
        if "issue_key" in payload and payload["issue_key"] not in ticket_ids:
            ticket_ids.append(payload["issue_key"])

        incident_ids = biz.get("incident_ids") or []
        if "incident_id" in payload and payload["incident_id"] not in incident_ids:
            incident_ids.append(payload["incident_id"])

        return BusinessContext(
            ticket_ids=ticket_ids,
            incident_ids=incident_ids,
            project_id=biz.get("project_id") or payload.get("project_id"),
            change_request_id=biz.get("change_request_id") or payload.get("change_request_id")
        )


def skill_normalize_ocsf_event(
    raw_event: Dict[str, Any],
    protected_registry: Optional[List[str]] = None,
    salt_key: Optional[bytes] = None
) -> Optional[Dict[str, Any]]:
    """Procedural implementation of Skill 1 from skills.md."""
    custom_registry = None
    if protected_registry:
        from backend.ingestion.protected_filter import ProtectedRule
        rules = [
            ProtectedRule(
                rule_id=f"CUSTOM-{i}",
                pattern=pat,
                category="CUSTOM_PROTECTED",
                description="Custom protected pattern"
            )
            for i, pat in enumerate(protected_registry)
        ]
        custom_registry = ProtectedEndpointRegistry(initial_rules=rules)

    normalizer = OCSFEventNormalizer(
        protected_registry=custom_registry,
        salt_key=salt_key
    )

    canonical, filter_res = normalizer.normalize_event(raw_event)
    if filter_res.is_protected or canonical is None:
        return None

    return canonical.model_dump()
