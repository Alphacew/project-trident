"use client";

import React, { useState } from "react";
import { KeyRound, ShieldCheck, UserCheck, AlertOctagon, CheckCircle2, Clock } from "lucide-react";
import { PrivacyVaultStatus, RevealReceipt, ShamirShare } from "@/lib/types";

interface ShamirCeremonyCardProps {
  vaultStatus: PrivacyVaultStatus;
  onExecuteCeremony: (
    shares: number[],
    subjectToken: string,
    justification: string,
    auditorToken: string
  ) => Promise<RevealReceipt | null>;
}

export const ShamirCeremonyCard: React.FC<ShamirCeremonyCardProps> = ({
  vaultStatus,
  onExecuteCeremony,
}) => {
  const [selectedShares, setSelectedShares] = useState<number[]>([1, 2]); // default 2 shares selected
  const [subjectToken, setSubjectToken] = useState<string>("Subject-Theta-482");
  const [justification, setJustification] = useState<string>(
    "Tier 4 Critical insider breach investigation authorized by Legal & Works Council"
  );
  const [auditorToken, setAuditorToken] = useState<string>("DPO-Session-2026-09A");
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [revealedReceipt, setRevealedReceipt] = useState<RevealReceipt | null>(null);

  const toggleShare = (index: number) => {
    if (selectedShares.includes(index)) {
      setSelectedShares(selectedShares.filter((i) => i !== index));
    } else {
      setSelectedShares([...selectedShares, index]);
    }
  };

  const handleRun = async () => {
    if (selectedShares.length < 2) return;
    setIsExecuting(true);
    try {
      const receipt = await onExecuteCeremony(selectedShares, subjectToken, justification, auditorToken);
      if (receipt) setRevealedReceipt(receipt);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="bg-slate-900/60 rounded-xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-cyan-400" />
            <h4 className="text-sm font-bold text-slate-100">
              Shamir 2-of-3 Dual-Custody Reveal Ceremony
            </h4>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              GF(2^256 + 297) Prime Field
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Pseudonyms can never be unmasked unilaterally. At least 2 of 3 authorized custodians must supply their cryptographic polynomial shares.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700">
            Vault State: <span className="text-emerald-400 font-bold">SEALED</span>
          </span>
        </div>
      </div>

      {/* Custodian Shares Selection (3 cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {vaultStatus.custodian_shares.map((share) => {
          const isSelected = selectedShares.includes(share.index);
          return (
            <div
              key={share.index}
              onClick={() => toggleShare(share.index)}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-cyan-950/40 border-cyan-400 shadow-md shadow-cyan-500/10"
                  : "bg-slate-950/60 border-slate-800 opacity-60 hover:opacity-90"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  Share {share.index}
                </span>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}}
                  aria-label={`Select Share ${share.index}`}
                  className="w-4 h-4 rounded text-cyan-500 accent-cyan-400 cursor-pointer"
                />
              </div>

              <div className="mt-2 space-y-0.5">
                <span className="text-xs font-bold font-mono text-slate-100 block">
                  {share.custodian_role.replace("_", " ")}
                </span>
                <p className="text-[11px] text-slate-400 font-sans">{share.custodian_name}</p>
              </div>

              <div className="mt-2 pt-2 border-t border-slate-800/80">
                <span className="text-[10px] font-mono text-slate-500 block truncate" title={share.value_hex}>
                  Share Key: {share.value_hex.substring(0, 14)}...
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Ceremony Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
        <div>
          <label className="text-xs font-mono text-slate-400 block mb-1">Subject Pseudonym Token</label>
          <input
            type="text"
            value={subjectToken}
            onChange={(e) => setSubjectToken(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div>
          <label className="text-xs font-mono text-slate-400 block mb-1">Legal / Compliance Justification</label>
          <input
            type="text"
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div>
          <label className="text-xs font-mono text-slate-400 block mb-1">DPO Audit Token</label>
          <input
            type="text"
            value={auditorToken}
            onChange={(e) => setAuditorToken(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
          />
        </div>
      </div>

      {/* Execute Button */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs font-mono text-slate-400">
          Selected Shares: <span className="text-cyan-400 font-bold">{selectedShares.length} of 3</span>
          {selectedShares.length < 2 && (
            <span className="text-rose-400 ml-2">⚠️ Minimum 2 distinct custodian shares required</span>
          )}
        </div>

        <button
          onClick={handleRun}
          disabled={selectedShares.length < 2 || isExecuting}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-bold bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 disabled:opacity-40 transition-all cursor-pointer"
        >
          <KeyRound className="w-4 h-4" />
          <span>{isExecuting ? "Reconstructing AES-256 Key..." : "Execute 2-of-3 Reveal Ceremony"}</span>
        </button>
      </div>

      {/* Reveal Result Banner */}
      {revealedReceipt && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/80 to-blue-950/80 border border-cyan-400/80 space-y-2 glow-cyan animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-mono font-bold text-emerald-300 uppercase">
                Dual Custody Authorization Verified & Unmasked
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-amber-300">
              <Clock className="w-3.5 h-3.5" />
              <span>Ephemeral Session TTL: 14:58 remaining</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Pseudonym Token</span>
              <span className="text-sm font-mono font-bold text-cyan-300">{revealedReceipt.subject_token}</span>
            </div>

            <div className="bg-slate-950/70 p-3 rounded-lg border border-cyan-500/40">
              <span className="text-[10px] font-mono uppercase text-cyan-400 block">Unmasked Real Identity</span>
              <span className="text-sm font-mono font-bold text-slate-100">{revealedReceipt.unmasked_identity}</span>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400 pt-1 space-y-0.5">
            <p>Receipt ID: <span className="text-slate-300">{revealedReceipt.receipt_id}</span></p>
            <p>Participating Custodians: <span className="text-slate-300">{revealedReceipt.participating_custodians.join(" + ")}</span></p>
            <p className="truncate" title={revealedReceipt.entry_hash}>
              SHA-256 Ledger Entry Hash: <span className="text-cyan-300 font-bold">{revealedReceipt.entry_hash}</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
