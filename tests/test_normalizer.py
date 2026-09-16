"""Unit tests for DevA: OCSF Event Normalizer (Skill 1)."""

import pytest
from datetime import datetime, timezone
from backend.common.schemas import EventType, IdentityType
from backend.ingestion.normalizer import OCSFEventNormalizer, skill_normalize_ocsf_event


def test_normalize_okta_event():
    norm = OCSFEventNormalizer()
    raw = {
        "eventType": "user.session.start",
        "actor": {
            "id": "00u123456789",
            "alternateId": "alice.turner@corp.internal"
        },
        "role": "SecurityEngineer",
        "department": "SecOps",
        "timestamp": "2026-09-10T14:30:00Z",
        "sourceIPAddress": "192.0.2.1",
        "resource_id": "okta:dashboard"
    }

    canonical, filter_res = norm.normalize_event(raw)
    assert canonical is not None
    assert filter_res.is_protected is False
    assert canonical.event_type == EventType.AUTHENTICATION
    assert canonical.actor.actor_token.startswith("Subject-")
    assert canonical.actor.raw_id is None  # Invariant 6: raw_id is never leaked
    assert canonical.actor.role == "SecurityEngineer"
    assert canonical.source_system == "okta"


def test_normalize_cloudtrail_event():
    norm = OCSFEventNormalizer()
    raw = {
        "eventSource": "s3.amazonaws.com",
        "eventName": "GetObject",
        "eventTime": "2026-09-10T15:00:00Z",
        "userIdentity": {
            "type": "AssumedRole",
            "arn": "arn:aws:sts::123456789012:assumed-role/DataPipelineRole/session-1"
        },
        "resources": [
            {"ARN": "arn:aws:s3:::prod-customer-pii-vault/export.parquet", "type": "AWS::S3::Object"}
        ],
        "sourceIPAddress": "10.100.4.12",
        "userAgent": "Boto3/1.34.0 Python/3.11"
    }

    canonical, filter_res = norm.normalize_event(raw)
    assert canonical is not None
    assert filter_res.is_protected is False
    assert canonical.actor.identity_type == IdentityType.SERVICE_ACCOUNT
    assert canonical.actor.actor_token.startswith("ServiceAccount-")
    assert canonical.resource.resource_id == "arn:aws:s3:::prod-customer-pii-vault/export.parquet"
    assert canonical.network.source_ip == "10.100.4.12"


def test_normalize_protected_event_dropped_from_graph():
    norm = OCSFEventNormalizer()
    raw = {
        "action": "http:post",
        "destination_endpoint": "https://whistleblower-portal.internal.corp/incident/submit",
        "actor_id": "whistleblower_user"
    }

    canonical, filter_res = norm.normalize_event(raw)
    assert canonical is None  # Dropped before graph ingestion
    assert filter_res.is_protected is True
    assert filter_res.action == "DROP_FROM_GRAPH"


def test_skill_normalize_ocsf_event_wrapper():
    raw = {
        "action": "db:select",
        "actor_id": "test_engineer",
        "resource_id": "db:prod-analytics",
        "sensitivity": 0.7
    }
    result = skill_normalize_ocsf_event(raw)
    assert result is not None
    assert "event_id" in result
    assert result["actor"]["actor_token"].startswith("Subject-")
