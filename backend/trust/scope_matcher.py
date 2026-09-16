"""Project TRIDENT — Scope Matcher
Evaluates semantic and topological correlation between an organizational anchor
(Jira ticket, ServiceNow change, etc.) and an accessed telemetry target resource.
Runs deterministically in sub-millisecond time with zero external API dependencies.
"""

import re
from typing import Set
from backend.trust.schemas import ContextAnchor, EventContextStub

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
    "by", "of", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "this", "that", "it", "as"
}

# Domain keyword clusters for semantic compatibility
DOMAIN_TAXONOMY = {
    "payroll": {"payroll", "salary", "salaries", "compensation", "hr", "bonus", "benefits", "w2", "tax"},
    "finance": {"finance", "billing", "invoice", "payments", "ledger", "stripe", "banking", "treasury"},
    "auth": {"auth", "oauth", "login", "sso", "saml", "credential", "jwt", "session", "okta"},
    "infrastructure": {"infra", "terraform", "k8s", "kubernetes", "cloudtrail", "aws", "vpc", "iam"},
    "frontend": {"frontend", "ui", "css", "react", "navbar", "dropdown", "button", "modal", "page"},
    "database": {"db", "database", "sql", "postgres", "mysql", "snowflake", "table", "schema", "query"},
}


def _tokenize(text: str) -> Set[str]:
    """Tokenize string into lowercase alphanumeric words, stripping stopwords."""
    if not text:
        return set()
    raw_tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    # Sub-split snake_case or dotted tokens
    expanded = []
    for t in raw_tokens:
        expanded.extend(t.replace("-", "_").replace(".", "_").split("_"))
    return {w for w in expanded if len(w) > 1 and w not in STOP_WORDS}


def _detect_domains(tokens: Set[str]) -> Set[str]:
    """Detect matching domain clusters for a set of tokens."""
    matched = set()
    for domain, keywords in DOMAIN_TAXONOMY.items():
        if tokens & keywords:
            matched.add(domain)
    return matched


def compute_scope_match(anchor: ContextAnchor, event: EventContextStub) -> float:
    """Computes scope match score between 0.0 (total mismatch) and 1.0 (exact match).
    
    1. Direct Resource Match: Target resource explicitly listed in anchor -> 1.0.
    2. Token Overlap: Jaccard similarity between resource tokens and ticket tokens.
    3. Domain Congruency: Checks if ticket and resource share functional domain.
    """
    target_clean = event.target_resource.strip().lower()

    # Rule 1: Exact target match
    for res in anchor.target_resources:
        if res.strip().lower() == target_clean:
            return 1.0
        if target_clean in res.strip().lower() or res.strip().lower() in target_clean:
            return 0.95

    # Rule 2: Tokenize resource and ticket text
    resource_tokens = _tokenize(event.target_resource)
    ticket_text = f"{anchor.title} {anchor.description} {' '.join(anchor.target_resources)}"
    ticket_tokens = _tokenize(ticket_text)

    if not resource_tokens:
        return 0.5  # Neutral fallback

    common_tokens = resource_tokens & ticket_tokens
    token_overlap_ratio = len(common_tokens) / len(resource_tokens)

    # If key resource tokens appear in the ticket (e.g., 'salaries' or 'payroll')
    if token_overlap_ratio >= 0.5:
        return min(1.0, 0.70 + token_overlap_ratio * 0.30)
    elif token_overlap_ratio > 0:
        return min(0.70, 0.40 + token_overlap_ratio * 0.40)

    # Rule 3: Domain taxonomy analysis
    res_domains = _detect_domains(resource_tokens)
    ticket_domains = _detect_domains(ticket_tokens)

    # If both have detected domains and they match
    if res_domains and ticket_domains:
        if res_domains & ticket_domains:
            return 0.65
        else:
            # Active domain conflict (e.g. ticket is 'frontend' and resource is 'payroll')
            return 0.05

    # Default low overlap score
    return 0.10
