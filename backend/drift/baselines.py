"""Project TRIDENT — Fast/Slow Behavioral Baselines & Dynamic Peer Cohorts
Maintains dual baselines (7-day fast and 90-day slow) with anti-poisoning weighting,
and clusters actors into dynamic peer cohorts.
"""

from typing import Dict, List, Optional
import numpy as np
from backend.drift.schemas import BaselineProfile, BehavioralFeatureVector

# Default peer cohort prototypes
COHORT_PROTOTYPES: Dict[str, BehavioralFeatureVector] = {
    "Engineering-Backend": BehavioralFeatureVector(
        event_volume_rate=1.0,
        resource_sensitivity_mean=0.25,
        new_resource_discovery_ratio=0.05,
        off_hours_ratio=0.05,
        action_privilege_intensity=0.10,
        cross_boundary_entropy=0.10,
    ),
    "Engineering-DevOps": BehavioralFeatureVector(
        event_volume_rate=2.2,
        resource_sensitivity_mean=0.45,
        new_resource_discovery_ratio=0.12,
        off_hours_ratio=0.15,
        action_privilege_intensity=0.35,
        cross_boundary_entropy=0.40,
    ),
    "Finance-Operations": BehavioralFeatureVector(
        event_volume_rate=0.8,
        resource_sensitivity_mean=0.60,
        new_resource_discovery_ratio=0.02,
        off_hours_ratio=0.02,
        action_privilege_intensity=0.15,
        cross_boundary_entropy=0.05,
    ),
    "NonHuman-CICDRunner": BehavioralFeatureVector(
        event_volume_rate=5.0,
        resource_sensitivity_mean=0.30,
        new_resource_discovery_ratio=0.01,
        off_hours_ratio=0.40,  # Scheduled night builds
        action_privilege_intensity=0.20,
        cross_boundary_entropy=0.15,
    ),
    "NonHuman-ServiceAccount": BehavioralFeatureVector(
        event_volume_rate=3.5,
        resource_sensitivity_mean=0.40,
        new_resource_discovery_ratio=0.01,
        off_hours_ratio=0.35,
        action_privilege_intensity=0.25,
        cross_boundary_entropy=0.20,
    ),
}


class BaselineManager:
    """Manages fast (7d) and slow (90d) individual baselines and dynamic peer cohorts."""

    def __init__(self, anti_poisoning_alpha: float = 0.35):
        """
        anti_poisoning_alpha: Weight given to fast 7d baseline vs slow 90d baseline.
        alpha=0.35 means 35% fast / 65% slow, resisting baseline poisoning attacks.
        """
        self.alpha = anti_poisoning_alpha
        self.profiles: Dict[str, BaselineProfile] = {}
        self.cohort_prototypes = COHORT_PROTOTYPES.copy()

    def register_cohort_prototype(self, name: str, vector: BehavioralFeatureVector) -> None:
        """Registers or overrides a peer cohort prototype."""
        self.cohort_prototypes[name] = vector

    def get_or_create_profile(
        self,
        actor_token: str,
        cohort_name: str = "Engineering-Backend",
        custom_slow_baseline: Optional[BehavioralFeatureVector] = None,
    ) -> BaselineProfile:
        """Retrieves or initializes a dual baseline profile for an actor."""
        if actor_token in self.profiles:
            return self.profiles[actor_token]

        cohort_vec = self.cohort_prototypes.get(
            cohort_name, self.cohort_prototypes["Engineering-Backend"]
        )
        slow_base = custom_slow_baseline or cohort_vec.model_copy()
        fast_base = slow_base.model_copy()

        profile = BaselineProfile(
            actor_token=actor_token,
            fast_baseline_7d=fast_base,
            slow_baseline_90d=slow_base,
            cohort_name=cohort_name,
            cohort_baseline=cohort_vec.model_copy(),
            cohort_drift_rate=0.10,
        )
        self.profiles[actor_token] = profile
        return profile

    def update_fast_baseline(
        self,
        actor_token: str,
        observations: List[BehavioralFeatureVector],
    ) -> BehavioralFeatureVector:
        """Updates the fast 7-day baseline using recent sliding observations."""
        profile = self.get_or_create_profile(actor_token)
        if not observations:
            return profile.fast_baseline_7d

        arrays = [obs.to_numpy() for obs in observations]
        mean_arr = np.mean(arrays, axis=0)
        profile.fast_baseline_7d = BehavioralFeatureVector.from_numpy(mean_arr)
        return profile.fast_baseline_7d

    def compute_effective_baseline(self, actor_token: str) -> BehavioralFeatureVector:
        """Computes the anti-poisoned effective baseline:
        z_effective = alpha * z_fast_7d + (1 - alpha) * z_slow_90d
        """
        profile = self.get_or_create_profile(actor_token)
        fast_arr = profile.fast_baseline_7d.to_numpy()
        slow_arr = profile.slow_baseline_90d.to_numpy()

        effective_arr = self.alpha * fast_arr + (1.0 - self.alpha) * slow_arr
        return BehavioralFeatureVector.from_numpy(effective_arr)
