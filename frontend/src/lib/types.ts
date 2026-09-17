/**
 * Project TRIDENT — Frontend TypeScript Data Contracts & Schemas
 * 
 * Defines all shared types used across:
 * - Screen 1: Dual Timeline & CUSUM Drift
 * - Screen 2: React Flow Minimal Causal Graph & Canary Deception
 * - Screen 3: Shamir 2-of-3 Privacy Vault & Anti-Harassment Guardrails
 */

export interface ScenarioMetadata {
  scenario_id: string;
  title: string;
  name?: string;
  description: string;
  duration_days: number;
  threat_type?: string;
  expected_tier?: string;
  mitre_tactics?: string[];
}

export interface ScenarioDaySnapshot {
  day: number;
  timestamp: string;
  raw_anomaly_score: number;
  context_authenticity_score: number;
  discount_factor: number;
  attenuated_anomaly_score: number;
  cusum_drift_score: number;
  drift_velocity: number;
  trajectory_state: string;
  composite_risk: number;
  risk_tier: string;
  canary_state: string;
  active_mitre_tactics: string[];
}

export interface ActorContext {
  actor_token: string;
  identity_type?: string;
  role?: string;
  department?: string;
  peer_group?: string;
}

export interface ResourceContext {
  resource_id: string;
  resource_type?: string;
  sensitivity: number;
  is_canary?: boolean;
}

export interface BusinessContext {
  ticket_ids: string[];
  change_request_ids?: string[];
  incident_ids?: string[];
}

export interface CanonicalEvent {
  event_id: string;
  timestamp: string;
  action: string;
  actor: ActorContext;
  resource: ResourceContext;
  business_context?: BusinessContext;
  raw_payload_hash: string;
  event_type?: string;
  source_system?: string;
}

export interface CausalNode {
  id: string;
  label: string;
  category: "ACTOR" | "CREDENTIAL" | "DATABASE" | "DISCOVERY" | "CANARY" | string;
  sensitivity: number;
  position?: { x: number; y: number };
}

export interface CausalEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  sensitivity: number;
  is_canary_trip?: boolean;
}

export interface CanaryDecoy {
  canary_id: string;
  resource_id: string;
  resource_type: string;
  created_at?: string;
  is_tripped: boolean;
  confirmation_state: "UNCONFIRMED" | "PREDICTED" | "CONFIRMED" | "PROBABILISTIC" | string;
  trip_timestamp?: string | null;
  tripped_by_actor?: string | null;
  predicted_threat_actor?: string | null;
  deployment_location?: string;
  claim_label?: string;
}

export interface ForensicProgressionStep {
  step_number: number;
  technique: string;
  timestamp: string;
  action: string;
  source_entity: string;
  target_entity: string;
  evidence_confidence: number;
  is_canary_trip?: boolean;
}

export interface MitreAttackItem {
  technique_id: string;
  technique_name: string;
  tactic: string;
  description: string;
  url?: string;
}

export interface ForensicDossier {
  incident_id: string;
  subject_token: string;
  risk_tier: string;
  composite_risk: number;
  trajectory_state: string;
  cusum_drift_score: number;
  context_justification_claimed: boolean;
  context_authenticity_score: number;
  anchor_discount_factor: number;
  context_failure_reasons: string[];
  progression_chain: ForensicProgressionStep[];
  mitre_attack_matrix: MitreAttackItem[];
  executive_summary: string;
  recommended_response_actions: string[];
  recommended_response?: string;
  canary_status?: CanaryDecoy;
  claim_label?: string;
}

export interface ShamirShare {
  custodian_role: string;
  custodian_name: string;
  index: number;
  value_hex: string;
}

export interface PrivacyVaultStatus {
  vault_status: string;
  threshold: string;
  active_subjects_count: number;
  demo_subject_token: string;
  custodian_shares: ShamirShare[];
  reveals_count: number;
  chain_head_hash?: string;
  chain_integrity?: string;
  active_harassment_alerts?: number;
  query_audits_count?: number;
  claim_label?: string;
}

export interface RevealReceipt {
  receipt_id: string;
  timestamp: string;
  subject_token: string;
  unmasked_identity: string;
  participating_custodians: string[];
  justification: string;
  auditor_token: string;
  previous_receipt_hash: string;
  entry_hash: string;
  verified_chain?: boolean;
  claim_label?: string;
}

export interface HarassmentAlert {
  alert_id: string;
  timestamp: string;
  dpo_notification: string;
  subject_token: string;
  analyst_id?: string;
  query_count: number;
  window_days?: number;
  current_risk_tier?: string;
  status: string;
  claim_label?: string;
}

export interface QueryValidationResult {
  allowed: boolean;
  query?: string;
  reason?: string | null;
  query_type: string;
  timestamp?: string;
}

export interface ProtectedRule {
  rule_id: string;
  pattern: string;
  category: string;
  description?: string;
}
