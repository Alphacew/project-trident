"use client";

import React, { useState } from "react";
import { UserX, ShieldAlert, AlertTriangle, CheckCircle2, Search } from "lucide-react";
import { HarassmentAlert, QueryValidationResult } from "@/lib/types";
import { api } from "@/lib/api";

interface AntiHarassmentCardProps {
  alerts: HarassmentAlert[];
}

export const AntiHarassmentCard: React.FC<AntiHarassmentCardProps> = ({ alerts }) => {
  const [testQuery, setTestQuery] = useState<string>("Elena Rostova");
  const [validationResult, setValidationResult] = useState<QueryValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  const handleTestQuery = async () => {
    setIsValidating(true);
    try {
      const res = await api.validateQuery(testQuery);
      setValidationResult(res);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="bg-slate-900/60 rounded-xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <UserX className="w-5 h-5 text-amber-400" />
          <div>
            <h4 className="text-sm font-bold text-slate-100">
              Anti-Harassment Governance & Surveillance Safeguards
            </h4>
            <p className="text-xs text-slate-400 font-sans">
              Prevents security tooling from being weaponized for arbitrary employee surveillance or managerial retaliation.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sub-panel 1: Interactive Query Guardrail Tester */}
        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
          <span className="text-xs font-mono font-bold uppercase text-slate-300 block">
            Guardrail 1: Direct Name Query Interceptor
          </span>
          <p className="text-[11px] text-slate-400 font-sans">
            Direct searches by employee name or email are blocked at the ingestion layer. Analysts may only query via anomaly IDs or pseudonyms.
          </p>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="e.g. Elena Rostova or Subject-Theta-482"
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-400"
            />
            <button
              onClick={handleTestQuery}
              disabled={isValidating}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-cyan-600 hover:bg-cyan-500 text-black transition"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Test Query</span>
            </button>
          </div>

          {/* Preset Buttons for Quick Judge Testing */}
          <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
            <span>Quick test:</span>
            <button
              onClick={() => setTestQuery("Elena Rostova")}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-rose-300 border border-rose-800/40"
            >
              "Elena Rostova" (Name)
            </button>
            <button
              onClick={() => setTestQuery("Subject-Theta-482")}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-800/40"
            >
              "Subject-Theta-482" (Token)
            </button>
          </div>

          {/* Validation Result Banner */}
          {validationResult && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono transition-all ${
                validationResult.allowed
                  ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-300"
                  : "bg-rose-950/50 border-rose-600/60 text-rose-300 glow-rose"
              }`}
            >
              <div className="flex items-center gap-2">
                {validationResult.allowed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <div>
                  <span className="font-bold uppercase">
                    {validationResult.allowed ? "QUERY PERMITTED" : "BLOCKED: DIRECT IDENTITY SEARCH PROHIBITED"}
                  </span>
                  <p className="text-[11px] font-sans mt-0.5">
                    {validationResult.reason ||
                      `Query target conforms to approved ${validationResult.query_type} specification.`}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sub-panel 2: Active DPO Repeat Subject Alerts */}
        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase text-slate-300 block">
              Guardrail 2: Repeat-Subject DPO Compliance Queue
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
              Threshold: &gt;3 Queries / 14 Days
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Automatically notifies Data Protection Officer when repeated manual reviews target a low-risk profile.
          </p>

          <div className="space-y-2 max-h-40 overflow-y-auto">
            {alerts.map((al) => (
              <div key={al.alert_id} className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-500/40 text-xs font-mono space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-300">{al.alert_id}</span>
                  <span className="text-[10px] text-slate-400">{new Date(al.timestamp).toLocaleDateString()}</span>
                </div>
                <p className="text-[11px] text-slate-300 font-sans">{al.dpo_notification}</p>
                <div className="flex items-center gap-3 text-[10px] text-slate-400 pt-1 border-t border-amber-800/30">
                  <span>Subject: <strong className="text-cyan-300">{al.subject_token}</strong></span>
                  <span>Inspections: <strong className="text-amber-400">{al.query_count}</strong></span>
                  <span>Status: <strong className="text-rose-400">{al.status}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
