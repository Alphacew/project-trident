"""Project TRIDENT — Deterministic MITRE ATT&CK Mapper.

Provides deterministic mapping of temporal graph events and progression steps
to MITRE ATT&CK Enterprise techniques:
- T1078: Valid Accounts (Initial Access / Defense Evasion)
- T1068: Exploitation for Privilege Escalation (Privilege Escalation)
- T1087: Account Discovery / T1083: File and Directory Discovery (Discovery)
- T1005: Data from Local System (Collection)
- T1074: Data Staged (Collection)
- T1567: Exfiltration Over Web Service (Exfiltration)

Invariant: Deterministic, rule-driven mapping without LLM hallucination.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from backend.evidence.schemas import ProgressionStage
from backend.graph.schemas import EdgeType


class DeterministicMitreMapper:
    """Maps security events and progression stages to MITRE ATT&CK techniques."""

    TACTIC_MAPPING: Dict[str, Dict[str, str]] = {
        "T1078": {
            "technique_id": "T1078",
            "name": "Valid Accounts",
            "tactic": "Initial Access & Defense Evasion",
            "description": "Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.",
            "url": "https://attack.mitre.org/techniques/T1078/",
        },
        "T1068": {
            "technique_id": "T1068",
            "name": "Exploitation for Privilege Escalation",
            "tactic": "Privilege Escalation",
            "description": "Adversaries may exploit software vulnerabilities or assume privileged IAM roles in an attempt to gain higher levels of permissions.",
            "url": "https://attack.mitre.org/techniques/T1068/",
        },
        "T1087": {
            "technique_id": "T1087",
            "name": "Account Discovery",
            "tactic": "Discovery",
            "description": "Adversaries may attempt to get a listing of accounts on a system or within an enterprise environment to identify high-privilege targets.",
            "url": "https://attack.mitre.org/techniques/T1087/",
        },
        "T1083": {
            "technique_id": "T1083",
            "name": "File and Directory Discovery",
            "tactic": "Discovery",
            "description": "Adversaries may enumerate files and directories or query repository listings to discover sensitive data stores.",
            "url": "https://attack.mitre.org/techniques/T1083/",
        },
        "T1005": {
            "technique_id": "T1005",
            "name": "Data from Local System",
            "tactic": "Collection",
            "description": "Adversaries may search for and access sensitive data from databases, repositories, or local file systems prior to exfiltration.",
            "url": "https://attack.mitre.org/techniques/T1005/",
        },
        "T1074": {
            "technique_id": "T1074",
            "name": "Data Staged",
            "tactic": "Collection",
            "description": "Adversaries may stage collected data in a central location or temporary mount prior to exfiltration.",
            "url": "https://attack.mitre.org/techniques/T1074/",
        },
        "T1567": {
            "technique_id": "T1567",
            "name": "Exfiltration Over Web Service",
            "tactic": "Exfiltration",
            "description": "Adversaries may steal data by exfiltrating it over an external web service, decoy endpoint, or cloud repository.",
            "url": "https://attack.mitre.org/techniques/T1567/",
        },
    }

    def map_stage_to_mitre(self, stage: ProgressionStage) -> Tuple[str, str]:
        """Maps a ProgressionStage to (MITRE Tactic, MITRE Technique)."""
        stage_map = {
            ProgressionStage.CREDENTIAL_ANOMALY: ("Initial Access", "T1078 (Valid Accounts)"),
            ProgressionStage.PRIVILEGE_ESCALATION: ("Privilege Escalation", "T1068 (Exploitation for Privilege Escalation)"),
            ProgressionStage.DISCOVERY: ("Discovery", "T1083 (File and Directory Discovery)"),
            ProgressionStage.SENSITIVE_ACCESS: ("Collection", "T1005 (Data from Local System)"),
            ProgressionStage.STAGING: ("Collection", "T1074 (Data Staged)"),
            ProgressionStage.CANARY_TRIP: ("Exfiltration", "T1567 (Exfiltration Over Web Service)"),
            ProgressionStage.EXFILTRATION: ("Exfiltration", "T1567 (Exfiltration Over Web Service)"),
        }
        return stage_map.get(stage, ("Initial Access", "T1078 (Valid Accounts)"))

    def map_edge_to_mitre(
        self,
        edge_type: EdgeType,
        target_resource: str,
        sensitivity: float,
        is_canary: bool = False,
    ) -> Tuple[str, str]:
        """Infers deterministic MITRE technique from edge type and target metadata."""
        if is_canary or edge_type == EdgeType.CANARY_TRIP:
            return ("Exfiltration", "T1567 (Exfiltration Over Web Service)")

        if edge_type == EdgeType.EXFILTRATED:
            return ("Exfiltration", "T1567 (Exfiltration Over Web Service)")

        if edge_type == EdgeType.STAGED or "staging" in target_resource.lower() or "tmpfs" in target_resource.lower():
            return ("Collection", "T1074 (Data Staged)")

        if edge_type == EdgeType.ASSUMED_ROLE or "role" in target_resource.lower() or "iam" in target_resource.lower():
            return ("Privilege Escalation", "T1068 (Exploitation for Privilege Escalation)")

        if edge_type in [EdgeType.QUERIED, EdgeType.MODIFIED] or "db:" in target_resource or sensitivity >= 0.7:
            return ("Collection", "T1005 (Data from Local System)")

        if edge_type == EdgeType.ACCESSED and ("repo:" in target_resource or "arn:aws:s3" in target_resource):
            return ("Discovery", "T1083 (File and Directory Discovery)")

        if edge_type == EdgeType.AUTHENTICATED:
            return ("Initial Access", "T1078 (Valid Accounts)")

        return ("Discovery", "T1087 (Account Discovery)")

    def get_technique_details(self, technique_id: str) -> Optional[Dict[str, str]]:
        """Returns MITRE dictionary entry for a technique ID."""
        tech_clean = technique_id.split()[0]
        return self.TACTIC_MAPPING.get(tech_clean)

    def generate_matrix(self, technique_ids: List[str]) -> List[Dict[str, str]]:
        """Generates structured MITRE ATT&CK table for forensic dossiers."""
        matrix = []
        seen = set()
        for t in technique_ids:
            tech_clean = t.split()[0]
            if tech_clean in self.TACTIC_MAPPING and tech_clean not in seen:
                seen.add(tech_clean)
                matrix.append(self.TACTIC_MAPPING[tech_clean])
        return matrix
