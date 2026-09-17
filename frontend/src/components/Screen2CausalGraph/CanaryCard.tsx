"use client";

import React, { useState } from "react";
import { ShieldAlert, Zap, CheckCircle, Radio } from "lucide-react";
import { CanaryDecoy } from "@/lib/types";

interface CanaryCardProps {
  canaryStatus: CanaryDecoy;
  onTripCanary: () => void;
  isTripping: boolean;
}

export const CanaryCard: React.FC<CanaryCardProps> = ({
  canaryStatus,
  onTripCanary,
  isTripping,
}) => {
  const isTripped = canaryStatus.is_tripped;

  return (
    <div
      className={`rounded-xl border p-4 transition-all ${
        isTripped
          ? "bg-rose-950/30 border-rose-600/60 shadow-lg shadow-rose-950/40"
          : "bg-slate-900/60 border-slate-800"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center ${
              isTripped
                ? "bg-rose-500/20 text-rose-400 border border-rose-500/50"
                : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50"
            }`}
          >
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">Simulated Canary Deception Decoy</h4>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Simulated Canary
              </span>
            </div>
            <p className="text-xs font-mono text-slate-400">{canaryStatus.resource_id}</p>
          </div>
        </div>

        {/* State Badge */}
        <div>
          {isTripped ? (
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/60 flex items-center gap-1.5 animate-pulse">
              <Radio className="w-3.5 h-3.5 text-rose-500" />
              CONFIRMED (DETERMINISTIC)
            </span>
          ) : (
            <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              ARMED (PROBABILISTIC)
            </span>
          )}
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-300 font-sans leading-relaxed">
        {isTripped
          ? "Forensic evidence confirms Subject-Theta-482 accessed the decoy asset. Threat state transitioned deterministically to CONFIRMED. Probabilistic suspicion is resolved; Tier 4 escalation is authorized."
          : "Active honeypot decoy deployed along the projected risk trajectory. If the actor attempts unanchored lateral exfiltration into this target, confirmation flips immediately to deterministic proof."}
      </p>

      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <div className="text-[11px] font-mono text-slate-400">
          <span>Deployment Location: </span>
          <span className="text-slate-300 font-semibold">{canaryStatus.deployment_location}</span>
        </div>

        {!isTripped ? (
          <button
            onClick={onTripCanary}
            disabled={isTripping}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-md shadow-rose-600/30 transition-all disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{isTripping ? "Tripping Canary..." : "Trip Canary Decoy (Beat 4)"}</span>
          </button>
        ) : (
          <div className="flex items-center gap-1.5 text-xs font-mono text-rose-400 font-semibold">
            <CheckCircle className="w-4 h-4" />
            <span>Tripped at {canaryStatus.trip_timestamp ? new Date(canaryStatus.trip_timestamp).toLocaleTimeString() : "Day 13 03:12 UTC"}</span>
          </div>
        )}
      </div>
    </div>
  );
};
