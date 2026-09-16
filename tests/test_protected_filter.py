"""Unit tests for DevA: Protected Endpoint Filter (Invariant 1)."""

import pytest
from backend.ingestion.protected_filter import ProtectedEndpointRegistry, ProtectedFilter, ProtectedRule


def test_whistleblower_uri_drop():
    f = ProtectedFilter()
    event = {
        "action": "http:get",
        "destination_endpoint": "https://whistleblower.internal.corp/submit-report",
        "actor_id": "alice"
    }
    result = f.filter_event(event)
    assert result.is_protected is True
    assert result.action == "DROP_FROM_GRAPH"
    assert result.audit_receipt_id is not None
    assert "whistleblower" in result.matched_rule.lower()


def test_ombudsman_email_drop():
    f = ProtectedFilter()
    event = {
        "action": "email:send",
        "to": "ombudsman-office@internal.corp",
        "actor_id": "bob"
    }
    result = f.filter_event(event)
    assert result.is_protected is True
    assert result.action == "DROP_FROM_GRAPH"


def test_ethics_hotline_url_drop():
    f = ProtectedFilter()
    event = {
        "action": "web:navigate",
        "url": "https://ethics-hotline.secure.corp/form",
        "actor_id": "charlie"
    }
    result = f.filter_event(event)
    assert result.is_protected is True
    assert result.action == "DROP_FROM_GRAPH"


def test_cidr_ip_protected_drop():
    f = ProtectedFilter()
    event = {
        "action": "network:connect",
        "destination_ip": "198.51.100.42",
        "actor_id": "dave"
    }
    result = f.filter_event(event)
    assert result.is_protected is True
    assert result.action == "DROP_FROM_GRAPH"


def test_benign_business_event_allowed():
    f = ProtectedFilter()
    event = {
        "action": "git:push",
        "resource_id": "repo:core-backend",
        "destination_endpoint": "https://github.com/corp/core-backend",
        "actor_id": "eve"
    }
    result = f.filter_event(event)
    assert result.is_protected is False
    assert result.action == "ALLOW"
    assert result.audit_receipt_id is None


def test_tamper_resistant_registry_dual_authorization():
    reg = ProtectedEndpointRegistry()
    rule_id = "RULE-WHISTLEBLOWER-URI"
    
    # Attempt unauthorized removal
    success_unauth = reg.request_remove_rule(
        rule_id=rule_id,
        dpo_token="UNAUTHORIZED-TOKEN",
        works_council_token="NO-TOKEN",
        justification="Testing tampering"
    )
    assert success_unauth is False
    assert any(r.rule_id == rule_id for r in reg.get_rules())

    # Attempt with valid dual-auth tokens
    success_auth = reg.request_remove_rule(
        rule_id=rule_id,
        dpo_token="DPO-AUTH-SEC-992",
        works_council_token="WC-AUTH-APP-412",
        justification="Authorized legal policy revision"
    )
    assert success_auth is True
    assert not any(r.rule_id == rule_id for r in reg.get_rules())
    
    # Verify audit log captures the actions
    audit_log = reg.get_audit_log()
    assert len(audit_log) == 2
    assert audit_log[0].status == "FAILED_DUAL_AUTH"
    assert audit_log[1].status == "SUCCESS"
