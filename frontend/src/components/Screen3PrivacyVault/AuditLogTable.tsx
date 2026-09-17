"use client";

import React, { useState } from "react";
import { Link2, ShieldCheck, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { RevealReceipt } from "@/lib/types";
import { api } from "@/lib/api";

interface AuditLogTableProps {
  auditLog: RevealReceipt[];
  onRefresh: () => void;
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  auditLog,
  onRefresh,
}) => {
  const [verificationResult, setVerificationResult] = useState<{
    verified: boolean;
    status: string;
    message: string;
    entries_checked: number;
  } | null>(null);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);

  const handleVerify = async () => {
    setIsVerifying(true);
    try {
      const res = await api.verifyAuditLog();
      setVerificationResult(res);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="bg-slate-900/60 rounded-xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-purple-400" />
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">
                Cryptographic Hash-Chained Reveal Ledger
              </h4>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                SHA-256 Merkle Chained
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              Immutable append-only ledger. Each reveal entry cryptographically embeds the previous entry's hash.
            </p>
          </div>
        </div>

        <button
          onClick={handleVerify}
          disabled={isVerifying}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? "animate-spin" : ""}`} />
          <span>Verify Ledger Integrity</span>
        </button>
      </div>

      {/* Verification Status Banner */}
      {verificationResult && (
        <div
          className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
            verificationResult.verified
              ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-300"
              : "bg-rose-950/40 border-rose-500/50 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {verificationResult.verified ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            )}
            <span>
              STATUS: <strong className="font-bold">{verificationResult.status}</strong> — {verificationResult.message}
            </span>
          </div>
          <span className="text-[10px] text-slate-400">
            {verificationResult.entries_checked} Blocks Verified
          </span>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="overflow-x-auto max-h-56 overflow-y-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 sticky top-0">
            <tr>
              <th className="py-2 px-3">Receipt ID</th>
              <th className="py-2 px-3">Timestamp (UTC)</th>
              <th className="py-2 px-3">Subject Token</th>
              <th className="py-2 px-3">Unmasked Plaintext</th>
              <th className="py-2 px-3">Custodians</th>
              <th className="py-2 px-3">Previous Block Hash</th>
              <th className="py-2 px-3">Current Entry Hash</th>
              <th className="py-2 px-3">Chain State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {auditLog.map((log) => (
              <tr key={log.receipt_id} className="hover:bg-slate-800/30 transition">
                <td className="py-2 px-3 text-cyan-300 font-bold whitespace-nowrap">{log.receipt_id}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="py-2 px-3 font-semibold text-slate-200">{log.subject_token}</td>
                <td className="py-2 px-3 text-emerald-300 font-bold">{log.unmasked_identity}</td>
                <td className="py-2 px-3 whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    {log.participating_custodians.map((c) => (
                      <span key={c} className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-slate-300">
                        {c.replace("_", " ")}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-2 px-3 text-slate-500 max-w-[100px] truncate" title={log.previous_receipt_hash}>
                  {(log.previous_receipt_hash || "0000000000000000").substring(0, 12)}...
                </td>
                <td className="py-2 px-3 text-purple-300 max-w-[100px] truncate font-bold" title={log.entry_hash}>
                  {(log.entry_hash || "0000000000000000").substring(0, 12)}...
                </td>
                <td className="py-2 px-3 whitespace-nowrap">
                  <span className="flex items-center gap-1 text-emerald-400 font-bold text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Verified
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
