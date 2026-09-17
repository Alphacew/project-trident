"use client";

import React, { useEffect, useState } from "react";
import { ShamirCeremonyCard } from "./ShamirCeremonyCard";
import { AuditLogTable } from "./AuditLogTable";
import { AntiHarassmentCard } from "./AntiHarassmentCard";
import { ProtectedRegistryCard } from "./ProtectedRegistryCard";
import { HarassmentAlert, PrivacyVaultStatus, RevealReceipt } from "@/lib/types";
import { api } from "@/lib/api";
import { MOCK_HARASSMENT_ALERTS, MOCK_PRIVACY_VAULT_STATUS, MOCK_REVEAL_AUDIT_LOG } from "@/lib/mockData";

export const PrivacyVaultView: React.FC = () => {
  const [vaultStatus, setVaultStatus] = useState<PrivacyVaultStatus>(MOCK_PRIVACY_VAULT_STATUS);
  const [auditLog, setAuditLog] = useState<RevealReceipt[]>(MOCK_REVEAL_AUDIT_LOG);
  const [alerts, setAlerts] = useState<HarassmentAlert[]>(MOCK_HARASSMENT_ALERTS);

  const loadData = () => {
    api.getPrivacyVaultStatus().then(setVaultStatus);
    api.getAuditLog().then(setAuditLog);
    api.getHarassmentAlerts().then(setAlerts);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteCeremony = async (
    shares: number[],
    subjectToken: string,
    justification: string,
    auditorToken: string
  ): Promise<RevealReceipt | null> => {
    try {
      const receipt = await api.recombineShamirShares(shares, subjectToken, justification, auditorToken);
      if (receipt) {
        // Prepend to audit log
        setAuditLog((prev) => [receipt, ...prev]);
        // Dynamically update vault status
        setVaultStatus((prev) => ({
          ...prev,
          reveals_count: (prev.reveals_count || 0) + 1,
          chain_head_hash: receipt.entry_hash,
          vault_status: "UNMASKED_EPHEMERAL",
        }));
        return receipt;
      }
      return null;
    } catch (err) {
      console.error("Ceremony execution failed:", err);
      return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Shamir 2-of-3 Threshold Ceremony */}
      <ShamirCeremonyCard
        vaultStatus={vaultStatus}
        onExecuteCeremony={handleExecuteCeremony}
      />

      {/* 2. Hash-Chained Audit Ledger */}
      <AuditLogTable
        auditLog={auditLog}
        onRefresh={loadData}
      />

      {/* 3. Anti-Harassment Governance Safeguards */}
      <AntiHarassmentCard alerts={alerts} />

      {/* 4. Protected Endpoints Ingestion Registry */}
      <ProtectedRegistryCard />
    </div>
  );
};
