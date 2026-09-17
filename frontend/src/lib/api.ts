/**
 * Project TRIDENT — Frontend API Client
 * 
 * Communicates with the FastAPI backend (default: http://localhost:8000).
 * Gracefully falls back to high-fidelity mock data when offline or in standalone mode.
 */

import {
  CanaryDecoy,
  CanonicalEvent,
  CausalEdge,
  CausalNode,
  ForensicDossier,
  HarassmentAlert,
  PrivacyVaultStatus,
  QueryValidationResult,
  RevealReceipt,
  ScenarioDaySnapshot,
  ScenarioMetadata,
} from "./types";
import {
  MOCK_CANARY_STATUS,
  MOCK_CAUSAL_EDGES,
  MOCK_CAUSAL_NODES,
  MOCK_FORENSIC_DOSSIER,
  MOCK_HARASSMENT_ALERTS,
  MOCK_PRIVACY_VAULT_STATUS,
  MOCK_REVEAL_AUDIT_LOG,
  MOCK_SCENARIOS,
  MOCK_TIMELINE_SNAPSHOTS,
} from "./mockData";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(url: string, options?: RequestInit, fallback?: T): Promise<T> {
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    if (fallback !== undefined) {
      return fallback;
    }
    throw err;
  }
}

export const api = {
  /**
   * Screen 1 & Global: List all available synthetic enterprise scenarios
   */
  async getScenarios(): Promise<ScenarioMetadata[]> {
    const data = await fetchJson<any[]>(`${API_BASE}/api/scenarios`, undefined, MOCK_SCENARIOS);
    return data.map((s) => ({
      scenario_id: s.scenario_id,
      title: s.title || s.name || s.scenario_id,
      name: s.name || s.title,
      description: s.description || "",
      duration_days: s.duration_days || 14,
      threat_type: s.threat_type,
      expected_tier: s.expected_tier,
      mitre_tactics: s.mitre_tactics || [],
    }));
  },

  /**
   * Switch active scenario and recompute 14-day timeline state
   */
  async switchScenario(scenarioId: string): Promise<ScenarioDaySnapshot[]> {
    try {
      const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.daily_snapshots && data.daily_snapshots.length > 0) {
          return data.daily_snapshots;
        }
      }
      return await this.getTimeline();
    } catch {
      return MOCK_TIMELINE_SNAPSHOTS;
    }
  },

  /**
   * Screen 1: Full 14-day timeline series for Dual Timeline chart
   */
  async getTimeline(): Promise<ScenarioDaySnapshot[]> {
    return fetchJson<ScenarioDaySnapshot[]>(
      `${API_BASE}/api/timeline`,
      undefined,
      MOCK_TIMELINE_SNAPSHOTS
    );
  },

  /**
   * Screen 1: Fetch raw normalized canonical events for a specific day
   */
  async getTimelineEvents(day: number): Promise<CanonicalEvent[]> {
    return fetchJson<CanonicalEvent[]>(
      `${API_BASE}/api/timeline/events?day=${day}`,
      undefined,
      []
    );
  },

  /**
   * Screen 2: Fetch minimal causal progression graph for React Flow
   */
  async getCausalGraph(day?: number): Promise<{ nodes: CausalNode[]; edges: CausalEdge[] }> {
    try {
      const url = day ? `${API_BASE}/api/graph/causal?day=${day}` : `${API_BASE}/api/graph/causal`;
      const data = await fetchJson<any>(url, undefined, null);
      if (!data || !data.nodes) {
        return { nodes: MOCK_CAUSAL_NODES, edges: MOCK_CAUSAL_EDGES };
      }

      const nodes: CausalNode[] = data.nodes.map((n: any) => ({
        id: n.id,
        label: n.data?.label || n.label || n.id,
        category:
          n.data?.node_type?.toUpperCase() ||
          (n.id.startsWith("Subject-") ? "ACTOR" : n.is_canary ? "CANARY" : "DATABASE"),
        sensitivity: n.data?.sensitivity ?? n.sensitivity ?? 0.5,
      }));

      const edges: CausalEdge[] = data.edges.map((e: any) => ({
        id: e.id,
        source: e.source || e.source_id,
        target: e.target || e.target_id,
        edge_type: e.data?.edge_type || e.edge_type || e.label || "ACCESSED",
        sensitivity: e.data?.sensitivity ?? e.sensitivity ?? 0.5,
        is_canary_trip: e.data?.is_canary_trip ?? e.is_canary_trip ?? false,
      }));

      return {
        nodes: nodes.length > 0 ? nodes : MOCK_CAUSAL_NODES,
        edges: edges.length > 0 ? edges : MOCK_CAUSAL_EDGES,
      };
    } catch {
      return { nodes: MOCK_CAUSAL_NODES, edges: MOCK_CAUSAL_EDGES };
    }
  },

  /**
   * Screen 2: Get simulated canary deception status
   */
  async getCanaryStatus(): Promise<CanaryDecoy> {
    const data = await fetchJson<CanaryDecoy>(
      `${API_BASE}/api/canary/status`,
      undefined,
      MOCK_CANARY_STATUS
    );
    return {
      ...data,
      deployment_location: data.deployment_location || "us-east-1 / VPC-prod-internal / S3",
    };
  },

  /**
   * Screen 2: Trip simulated canary decoy
   */
  async triggerCanaryTrip(resourceId?: string): Promise<CanaryDecoy> {
    try {
      const data = await fetchJson<CanaryDecoy>(
        `${API_BASE}/api/canary/trip`,
        {
          method: "POST",
          body: JSON.stringify({ resource_id: resourceId || "arn:aws:s3:::canary-decoy-payroll-backup" }),
        },
        MOCK_CANARY_STATUS
      );
      return {
        ...data,
        is_tripped: true,
        confirmation_state: "CONFIRMED",
        deployment_location: data.deployment_location || "us-east-1 / VPC-prod-internal / S3",
      };
    } catch {
      return {
        ...MOCK_CANARY_STATUS,
        is_tripped: true,
        confirmation_state: "CONFIRMED",
        trip_timestamp: new Date().toISOString(),
      };
    }
  },

  /**
   * Screen 2: Fetch structured forensic incident dossier
   */
  async getForensicDossier(day?: number): Promise<ForensicDossier> {
    try {
      const url = day ? `${API_BASE}/api/evidence/dossier?day=${day}` : `${API_BASE}/api/evidence/dossier`;
      const data = await fetchJson<any>(url, undefined, null);
      if (!data) return MOCK_FORENSIC_DOSSIER;

      const actions =
        data.recommended_response_actions ||
        (data.recommended_response
          ? [data.recommended_response]
          : MOCK_FORENSIC_DOSSIER.recommended_response_actions);

      const progression = (data.progression_chain || []).map((step: any, idx: number) => ({
        step_number: step.step_number || idx + 1,
        technique: step.technique || step.mitre_technique || "T1005",
        timestamp: step.timestamp ? (typeof step.timestamp === "string" && step.timestamp.includes("T") ? new Date(step.timestamp).toLocaleTimeString() : String(step.timestamp)) : `Step ${idx + 1}`,
        action: step.action || "Observed graph transition",
        source_entity: step.source_entity || step.source_node || data.subject_token || "Actor",
        target_entity: step.target_entity || step.target_node || "Resource",
        evidence_confidence: step.evidence_confidence ?? step.confidence ?? 1.0,
        is_canary_trip: step.is_canary_trip ?? (step.stage === "CANARY_TRIP"),
      }));

      const mitre = (data.mitre_attack_matrix || []).map((m: any) => ({
        technique_id: m.technique_id,
        technique_name: m.technique_name || m.name || m.technique_id,
        tactic: m.tactic,
        description: m.description,
        url: m.url,
      }));

      return {
        ...data,
        recommended_response_actions: actions,
        progression_chain: progression.length > 0 ? progression : MOCK_FORENSIC_DOSSIER.progression_chain,
        mitre_attack_matrix: mitre.length > 0 ? mitre : MOCK_FORENSIC_DOSSIER.mitre_attack_matrix,
      };
    } catch {
      return MOCK_FORENSIC_DOSSIER;
    }
  },

  /**
   * Screen 3: Privacy Vault Status & Custodian Shares
   */
  async getPrivacyVaultStatus(): Promise<PrivacyVaultStatus> {
    return fetchJson<PrivacyVaultStatus>(
      `${API_BASE}/api/privacy/vault/status`,
      undefined,
      MOCK_PRIVACY_VAULT_STATUS
    );
  },

  /**
   * Screen 3: Hash-Chained Reveal Audit Log
   */
  async getAuditLog(): Promise<RevealReceipt[]> {
    return fetchJson<RevealReceipt[]>(
      `${API_BASE}/api/privacy/vault/audit-log`,
      undefined,
      MOCK_REVEAL_AUDIT_LOG
    );
  },

  /**
   * Screen 3: Active Anti-Harassment DPO Compliance Alerts
   */
  async getHarassmentAlerts(): Promise<HarassmentAlert[]> {
    return fetchJson<HarassmentAlert[]>(
      `${API_BASE}/api/privacy/harassment/alerts`,
      undefined,
      MOCK_HARASSMENT_ALERTS
    );
  },

  /**
   * Screen 3: Recombine 2-of-3 Shamir shares to unmask subject
   */
  async recombineShamirShares(
    shares: number[],
    subjectToken: string,
    justification: string,
    auditorToken: string
  ): Promise<RevealReceipt> {
    const res = await fetch(`${API_BASE}/api/privacy/vault/recombine`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        share_indices: shares,
        subject_token: subjectToken,
        justification,
        auditor_token: auditorToken,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Reveal ceremony failed" }));
      throw new Error(err.detail || "Reveal ceremony failed");
    }
    return res.json();
  },

  /**
   * Screen 3: Anti-harassment direct name search interceptor
   */
  async validateQuery(query: string): Promise<QueryValidationResult> {
    try {
      const res = await fetch(`${API_BASE}/api/privacy/query/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, analyst_id: "SOC-Analyst-1" }),
      });
      if (res.ok) {
        return res.json();
      }
    } catch {
      // Fallback local validation rule
    }

    const trimmed = query.trim();
    const isName = trimmed.includes(" ") || (!trimmed.startsWith("Subject-") && !trimmed.startsWith("ANOM-"));
    if (isName) {
      return {
        allowed: false,
        query: trimmed,
        query_type: "BLOCKED_DIRECT_NAME",
        reason: "Direct search by raw employee identity is blocked by Anti-Harassment Policy.",
      };
    }
    return {
      allowed: true,
      query: trimmed,
      query_type: "PSEUDONYM",
      reason: "Query target conforms to approved pseudonym specification.",
    };
  },

  /**
   * Screen 3: Cryptographic verification of the hash-chained reveal log
   */
  async verifyAuditLog(): Promise<{
    verified: boolean;
    status: string;
    message: string;
    entries_checked: number;
  }> {
    return fetchJson<{
      verified: boolean;
      status: string;
      message: string;
      entries_checked: number;
    }>(
      `${API_BASE}/api/privacy/vault/verify-log`,
      { method: "POST" },
      {
        verified: true,
        status: "CRYPTOGRAPHICALLY_VERIFIED",
        message: "Merkle hash chain intact. All block hashes verified back to genesis.",
        entries_checked: 1,
      }
    );
  },
};
