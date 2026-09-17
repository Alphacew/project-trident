"use client";

import React, { useState } from "react";
import { FileText, ShieldAlert, CheckCircle2, ChevronRight, AlertOctagon } from "lucide-react";
import { ForensicDossier } from "@/lib/types";

interface ForensicDossierCardProps {
  dossier: ForensicDossier;
}

export const ForensicDossierCard: React.FC<ForensicDossierCardProps> = ({ dossier }) => {
  const [activeTab, setActiveTab] = useState<"summary" | "progression" | "mitre">("summary");

  return (
    <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h4 className="text-sm font-bold text-slate-100">Forensic Incident Dossier & ATT&CK Matrix</h4>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
            {dossier.incident_id}
          </span>
        </div>

        {/* Mini Tab Switcher */}
        <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab("summary")}
            className={`px-2.5 py-1 rounded-md transition ${
              activeTab === "summary" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Executive Summary
          </button>
          <button
            onClick={() => setActiveTab("progression")}
            className={`px-2.5 py-1 rounded-md transition ${
              activeTab === "progression" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Progression Chain ({dossier.progression_chain.length})
          </button>
          <button
            onClick={() => setActiveTab("mitre")}
            className={`px-2.5 py-1 rounded-md transition ${
              activeTab === "mitre" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            MITRE Matrix ({dossier.mitre_attack_matrix.length})
          </button>
        </div>
      </div>

      {/* Tab 1: Executive Summary */}
      {activeTab === "summary" && (
        <div className="space-y-3">
          <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
            <span className="font-bold text-slate-100 block mb-1 font-mono uppercase text-[11px] text-cyan-400">
              Forensic Synthesis (Zero-LLM Deterministic Grounding):
            </span>
            {dossier.executive_summary}
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-mono font-bold uppercase text-slate-400 block">
              Recommended Tiered Containment Directives:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {dossier.recommended_response_actions.map((act, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-slate-950/50 rounded border border-slate-800 text-[11px] text-slate-300 font-mono">
                  <ChevronRight className="w-3.5 h-3.5 text-rose-400 mt-0.5 shrink-0" />
                  <span>{act}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Progression Chain */}
      {activeTab === "progression" && (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {dossier.progression_chain.map((step) => (
            <div
              key={step.step_number}
              className={`p-2.5 rounded-lg border text-xs font-mono flex items-start gap-3 transition ${
                step.is_canary_trip
                  ? "bg-rose-950/30 border-rose-600/60 text-rose-200"
                  : "bg-slate-950/60 border-slate-800 text-slate-300"
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] shrink-0 ${
                step.is_canary_trip ? "bg-rose-600 text-white" : "bg-slate-800 text-cyan-300"
              }`}>
                {step.step_number}
              </span>

              <div className="space-y-0.5 flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">{step.technique}</span>
                  <span className="text-[10px] text-slate-400">{step.timestamp}</span>
                </div>
                <p className="text-[11px] font-sans text-slate-300">{step.action}</p>
                <div className="flex items-center gap-2 pt-1 text-[10px] text-slate-400">
                  <span>Entity: {step.source_entity} → {step.target_entity}</span>
                  <span>•</span>
                  <span>Confidence: {(step.evidence_confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: MITRE ATT&CK Breakdown */}
      {activeTab === "mitre" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
          {dossier.mitre_attack_matrix.map((m) => (
            <div key={m.technique_id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold font-mono text-cyan-300">
                  {m.technique_id}: {m.technique_name}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-400 border border-rose-800 font-mono">
                  {m.tactic}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">{m.description}</p>
              <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono pt-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Causally Corroborated</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
