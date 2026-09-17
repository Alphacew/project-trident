"use client";

import React from "react";
import { ShieldCheck, Lock, CheckCircle2 } from "lucide-react";
import { MOCK_PROTECTED_RULES } from "@/lib/mockData";

export const ProtectedRegistryCard: React.FC = () => {
  return (
    <div className="bg-slate-900/60 rounded-xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">
                Protected-Endpoint Registry (Invariant 1: Ingestion Isolation)
              </h4>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                Pre-Graph Dropped (100%)
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              All communications touching ethics hotlines, ombudsman portals, or whistleblower channels are filtered before behavioral graph ingestion.
            </p>
          </div>
        </div>

        <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4" />
          Zero Leaks to Graph
        </span>
      </div>

      <div className="overflow-x-auto max-h-48 overflow-y-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 sticky top-0">
            <tr>
              <th className="py-2 px-3">Rule Identifier</th>
              <th className="py-2 px-3">Filter Pattern</th>
              <th className="py-2 px-3">Category</th>
              <th className="py-2 px-3">Ingestion Boundary Action</th>
              <th className="py-2 px-3">Graph Isolation State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {MOCK_PROTECTED_RULES.map((rule) => (
              <tr key={rule.rule_id} className="hover:bg-slate-800/30 transition">
                <td className="py-2 px-3 text-cyan-300 font-bold">{rule.rule_id}</td>
                <td className="py-2 px-3 text-amber-300 font-semibold">{rule.pattern}</td>
                <td className="py-2 px-3 text-slate-400">{rule.category}</td>
                <td className="py-2 px-3 text-rose-400 font-bold whitespace-nowrap">DROP_FROM_GRAPH</td>
                <td className="py-2 px-3 text-emerald-400 font-semibold whitespace-nowrap">
                  100% Filtered (Encrypted Audit Receipt)
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
