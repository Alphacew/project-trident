"""Project TRIDENT — Context Authenticity Score (CAS) Signal Evaluators
Implements the 10 mathematical signal evaluators s1 through s10.
Each evaluator outputs a SignalEvaluation with score in [-1.0, 1.0] and forensic rationale.
"""

from datetime import datetime, timezone
from typing import Dict
from backend.trust.schemas import ContextAnchor, EventContextStub, SignalEvaluation


DEFAULT_SIGNAL_WEIGHTS: Dict[str, float] = {
    "s1_temporal_mismatch": 1.5,
    "s2_approver_conflict": 1.2,
    "s3_emergency_abuse": 1.0,
    "s4_sod_violation": 1.5,
    "s5_stale_hr_metadata": 0.8,
    "s6_scope_mismatch": 1.4,
    "s7_cross_signal_inconsistency": 0.9,
    "s8_ticket_velocity_anomaly": 0.8,
    "s9_ghost_ticket": 1.3,
    "s10_post_hoc_modification": 1.4,
}


def eval_s1_temporal_mismatch(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s1_temporal_mismatch"],
) -> SignalEvaluation:
    """s1: Temporal distance between ticket creation and event.
    Ticket created < 5 minutes before action returns negative score.
    Ticket created after action returns -1.0 (retrofitting).
    """
    delta_seconds = (event.timestamp - anchor.created_at).total_seconds()
    delta_minutes = delta_seconds / 60.0

    if delta_minutes < 0:
        score = -1.0
        rationale = f"CRITICAL: Ticket created {abs(delta_minutes):.1f}m AFTER event occurred (retrofitted context)"
        flagged = True
    elif delta_minutes < 5.0:
        # Interpolate between -1.0 at 0 min and -0.2 at 4.99 min
        score = -1.0 + (delta_minutes / 5.0) * 0.8
        rationale = f"HIGH: Suspicious temporal proximity; ticket created only {delta_minutes:.1f}m before event"
        flagged = True
    elif delta_minutes <= 60.0:
        score = 0.5 + (delta_minutes - 5.0) / 55.0 * 0.5  # 0.5 to 1.0
        rationale = f"Normal temporal lead time ({delta_minutes:.1f}m before event)"
        flagged = False
    elif delta_minutes <= 1440.0:  # up to 24h
        score = 1.0
        rationale = f"Well-established ticket ({delta_minutes / 60.0:.1f}h before event)"
        flagged = False
    else:
        # Older ticket (decayed but still prior)
        days = delta_minutes / 1440.0
        score = max(0.2, 1.0 - (days - 1.0) * 0.1)
        rationale = f"Ticket is {days:.1f} days old (active standing context)"
        flagged = False

    return SignalEvaluation(
        signal_id="s1_temporal_mismatch",
        name="Temporal Mismatch",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s2_approver_conflict(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s2_approver_conflict"],
) -> SignalEvaluation:
    """s2: Requester and approver relationship.
    Direct reporting line or identical requester/approver returns negative score.
    """
    if anchor.is_self_approved or (
        anchor.approver_id and anchor.requester_id == anchor.approver_id
    ):
        score = -1.0
        rationale = "CRITICAL: Self-approval detected (requester == approver)"
        flagged = True
    elif anchor.requester_approver_reporting_dist == 0:
        score = -1.0
        rationale = "CRITICAL: Approver is identical to requester"
        flagged = True
    elif anchor.requester_approver_reporting_dist == 1:
        score = -0.4
        rationale = "MEDIUM: Approver and requester share direct hierarchical reporting line"
        flagged = True
    elif anchor.approver_id is not None:
        score = 1.0
        rationale = "Independent peer/manager approver verified"
        flagged = False
    else:
        # No formal approver specified
        score = 0.0
        rationale = "No explicit approver recorded for ticket"
        flagged = False

    return SignalEvaluation(
        signal_id="s2_approver_conflict",
        name="Approver Conflict",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s3_emergency_abuse(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s3_emergency_abuse"],
) -> SignalEvaluation:
    """s3: Frequency of emergency/expedited tickets by actor over 30 days exceeds cohort mean by > 2.5 sigma."""
    if not anchor.is_emergency:
        score = 0.8
        rationale = "Standard change path (non-emergency ticket)"
        flagged = False
    else:
        std = anchor.cohort_emergency_std_30d if anchor.cohort_emergency_std_30d > 0 else 0.5
        z_score = (anchor.actor_emergency_count_30d - anchor.cohort_emergency_mean_30d) / std

        if z_score > 2.5:
            score = -1.0
            rationale = (
                f"HIGH: Emergency abuse anomaly: actor used {anchor.actor_emergency_count_30d} "
                f"emergency tickets in 30d (z-score: {z_score:.2f} > 2.5σ)"
            )
            flagged = True
        elif z_score > 1.5:
            score = -0.4
            rationale = f"MEDIUM: Elevated emergency ticket rate (z-score: {z_score:.2f})"
            flagged = True
        else:
            score = 0.5
            rationale = f"Emergency ticket within expected statistical baseline (z-score: {z_score:.2f})"
            flagged = False

    return SignalEvaluation(
        signal_id="s3_emergency_abuse",
        name="Emergency Change Abuse",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s4_sod_violation(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s4_sod_violation"],
) -> SignalEvaluation:
    """s4: Separation-of-duties conflict (e.g. actor approved own access request)."""
    if anchor.is_self_approved:
        score = -1.0
        rationale = "CRITICAL: Separation of Duties violation: actor approved their own authorization request"
        flagged = True
    elif anchor.approver_id == event.actor_token:
        score = -1.0
        rationale = "CRITICAL: Separation of Duties violation: executing actor matches the approver"
        flagged = True
    else:
        score = 1.0
        rationale = "Separation of duties verified (distinct requester and approver)"
        flagged = False

    return SignalEvaluation(
        signal_id="s4_sod_violation",
        name="Separation of Duties",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s5_stale_hr_metadata(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s5_stale_hr_metadata"],
) -> SignalEvaluation:
    """s5: Access requested for previous team or deprecated project tag."""
    if anchor.is_stale_hr_project:
        score = -0.9
        rationale = "HIGH: Ticket associated with decommissioned or deprecated HR project tag"
        flagged = True
    elif (
        anchor.hr_project_tag
        and anchor.actor_current_project_tag
        and anchor.hr_project_tag != anchor.actor_current_project_tag
    ):
        score = -0.7
        rationale = (
            f"HIGH: Stale organizational context: ticket tagged for {anchor.hr_project_tag}, "
            f"but actor's active HR team is {anchor.actor_current_project_tag}"
        )
        flagged = True
    elif anchor.hr_project_tag:
        score = 1.0
        rationale = f"HR metadata verified: project tag {anchor.hr_project_tag} aligns with active team"
        flagged = False
    else:
        score = 0.0
        rationale = "No HR project metadata attached to anchor"
        flagged = False

    return SignalEvaluation(
        signal_id="s5_stale_hr_metadata",
        name="Stale HR Metadata",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s6_scope_mismatch(
    anchor: ContextAnchor,
    event: EventContextStub,
    scope_match_score: float,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s6_scope_mismatch"],
) -> SignalEvaluation:
    """s6: Semantic divergence between ticket description and accessed target resource/table."""
    # scope_match_score is in [0.0, 1.0] from scope_matcher
    if scope_match_score < 0.25:
        score = -1.0
        rationale = (
            f"CRITICAL: Scope mismatch ({scope_match_score:.2f}): accessed resource '{event.target_resource}' "
            f"has zero semantic correlation with ticket scope '{anchor.title}'"
        )
        flagged = True
    elif scope_match_score < 0.50:
        score = -0.5
        rationale = (
            f"MEDIUM: Low scope correlation ({scope_match_score:.2f}) between ticket and resource '{event.target_resource}'"
        )
        flagged = True
    elif scope_match_score < 0.75:
        score = 0.5
        rationale = f"Moderate scope match ({scope_match_score:.2f}) with target resource"
        flagged = False
    else:
        score = 1.0
        rationale = f"High scope alignment ({scope_match_score:.2f}) between ticket description and resource"
        flagged = False

    return SignalEvaluation(
        signal_id="s6_scope_mismatch",
        name="Scope Mismatch",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s7_cross_signal_inconsistency(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s7_cross_signal_inconsistency"],
) -> SignalEvaluation:
    """s7: Absence of correlated Slack/Teams discussions, PR reviews, or calendar meetings during event window."""
    total_corroborations = (
        anchor.corroborating_slack_messages_count
        + anchor.corroborating_pr_reviews_count
        + anchor.corroborating_calendar_events_count
    )

    if total_corroborations == 0:
        # If anchor is an emergency or high authority change, zero corroboration is suspect
        if anchor.is_emergency or anchor.authority_weight >= 0.8:
            score = -0.7
            rationale = "HIGH: Cross-signal inconsistency: zero Slack messages, PR reviews, or meetings corroborate this action"
            flagged = True
        else:
            score = -0.3
            rationale = "No corroborating communication or review signals found in event window"
            flagged = False
    elif total_corroborations == 1:
        score = 0.4
        rationale = "Single corroborating signal found (Slack/PR/meeting)"
        flagged = False
    else:
        score = 1.0
        rationale = f"Strong multi-channel corroboration ({total_corroborations} linked communications/reviews)"
        flagged = False

    return SignalEvaluation(
        signal_id="s7_cross_signal_inconsistency",
        name="Cross-Signal Inconsistency",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s8_ticket_velocity_anomaly(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s8_ticket_velocity_anomaly"],
) -> SignalEvaluation:
    """s8: Spurt of tickets created within a short window."""
    count = anchor.ticket_velocity_window_count
    if count >= 5:
        score = -1.0
        rationale = f"HIGH: Abnormal ticket burst velocity ({count} tickets created in 60m window)"
        flagged = True
    elif count >= 3:
        score = -0.4
        rationale = f"MEDIUM: Elevated ticket creation velocity ({count} tickets in window)"
        flagged = True
    else:
        score = 0.8
        rationale = f"Normal ticket creation velocity ({count} ticket in window)"
        flagged = False

    return SignalEvaluation(
        signal_id="s8_ticket_velocity_anomaly",
        name="Ticket Velocity Anomaly",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s9_ghost_ticket(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s9_ghost_ticket"],
) -> SignalEvaluation:
    """s9: Zero downstream commits, pull requests, deploy events, or status transitions following ticket."""
    downstream = (
        anchor.downstream_commits_count
        + anchor.downstream_prs_count
        + anchor.downstream_deploys_count
    )

    if downstream == 0:
        score = -1.0
        rationale = "CRITICAL: Ghost ticket detected: zero downstream commits, PRs, or deployments attached"
        flagged = True
    elif downstream == 1:
        score = 0.5
        rationale = "Downstream engineering artifact linked (1 commit/PR/deploy)"
        flagged = False
    else:
        score = 1.0
        rationale = f"Legitimate downstream engineering trace verified ({downstream} commits/PRs/deploys)"
        flagged = False

    return SignalEvaluation(
        signal_id="s9_ghost_ticket",
        name="Ghost Ticket",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )


def eval_s10_post_hoc_modification(
    anchor: ContextAnchor,
    event: EventContextStub,
    weight: float = DEFAULT_SIGNAL_WEIGHTS["s10_post_hoc_modification"],
) -> SignalEvaluation:
    """s10: Ticket updated, retrofitted, or re-scoped after anomalous behavior occurred."""
    # Check 1: was the ticket created after the event?
    if event.timestamp < anchor.created_at:
        score = -1.0
        rationale = "CRITICAL: Post-hoc creation: ticket was opened AFTER the event already took place"
        flagged = True
    # Check 2: was ticket updated after the event?
    elif anchor.updated_at and anchor.updated_at > event.timestamp:
        score = -0.9
        delta_m = (anchor.updated_at - event.timestamp).total_seconds() / 60.0
        rationale = f"HIGH: Post-hoc modification: ticket was edited/re-scoped {delta_m:.1f}m after event"
        flagged = True
    else:
        score = 1.0
        rationale = "Ticket creation and modifications strictly precede event"
        flagged = False

    return SignalEvaluation(
        signal_id="s10_post_hoc_modification",
        name="Post-Hoc Modification",
        score=round(score, 3),
        weight=weight,
        rationale=rationale,
        is_flagged=flagged,
    )
