"use client";

import React from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, ShieldAlert, Sparkles } from "lucide-react";
import { ScenarioDaySnapshot } from "@/lib/types";

interface DayScrubberProps {
  selectedDay: number;
  setSelectedDay: (day: number) => void;
  timeline: ScenarioDaySnapshot[];
}

export const DayScrubber: React.FC<DayScrubberProps> = ({
  selectedDay,
  setSelectedDay,
  timeline,
}) => {
  const getBeatInfo = (day: number) => {
    switch (day) {
      case 5:
        return {
          title: "Beat 2: Benign Anomaly Suppressed",
          desc: "Valid Jira ticket JIRA-PROJ-841 verified. High CAS (0.82) attenuates anomaly by 78% (δ=0.22).",
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
          color: "border-emerald-500/60 bg-emerald-950/40 text-emerald-300",
        };
      case 9:
        return {
          title: "Beat 2: Silent Drift Begins",
          desc: "Sub-threshold queries repeated without business anchor. CUSUM accumulator starts tracking low-and-slow drift.",
          icon: <AlertCircle className="w-4 h-4 text-yellow-400" />,
          color: "border-yellow-500/60 bg-yellow-950/40 text-yellow-300",
        };
      case 10:
        return {
          title: "Beat 3: Fabricated Context Rejected",
          desc: "Self-approved ticket created 4m prior with zero downstream PRs. CAS collapses to 0.21. Suppression denied!",
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          color: "border-amber-500/60 bg-amber-950/40 text-amber-300",
        };
      case 12:
        return {
          title: "Beat 4: Sensitive Staging",
          desc: "Bulk customer records staged to RAM disk /dev/shm. Trajectory predicts lateral exfiltration path.",
          icon: <AlertTriangle className="w-4 h-4 text-orange-400" />,
          color: "border-orange-500/60 bg-orange-950/40 text-orange-300",
        };
      case 13:
        return {
          title: "Beat 4: Simulated Canary Tripped",
          desc: "Decoy bucket accessed! Confirmation state flips from PROBABILISTIC to CONFIRMED deterministic proof.",
          icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
          color: "border-rose-500/60 bg-rose-950/40 text-rose-300",
        };
      case 14:
        return {
          title: "Beat 5: Escalation & Unmasking",
          desc: "Tier 4 Critical alert raised with deterministic causal dossier. Ready for Shamir 2-of-3 threshold reveal.",
          icon: <Sparkles className="w-4 h-4 text-rose-400" />,
          color: "border-rose-600 bg-rose-950/60 text-rose-200",
        };
      default:
        return null;
    }
  };

  const activeBeat = getBeatInfo(selectedDay);

  return (
    <div className="w-full bg-slate-900/60 rounded-xl p-4 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400">
          14-Day Chronological Timeline & Hackathon Demo Beats
        </h4>
        <span className="text-xs font-mono text-cyan-400">Day {selectedDay} of 14</span>
      </div>

      {/* Slider Bar */}
      <input
        type="range"
        min={1}
        max={14}
        value={selectedDay}
        onChange={(e) => setSelectedDay(parseInt(e.target.value))}
        aria-label="Timeline Day Scrubber"
        className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
      />

      {/* Day Cards with markers */}
      <div className="grid grid-cols-7 sm:grid-cols-14 gap-1.5">
        {Array.from({ length: 14 }, (_, i) => i + 1).map((d) => {
          const snap = timeline[d - 1];
          const isSelected = selectedDay === d;
          const isKeyBeat = d === 5 || d === 9 || d === 10 || d === 13 || d === 14;

          return (
            <button
              key={d}
              onClick={() => setSelectedDay(d)}
              className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all text-center ${
                isSelected
                  ? "border-cyan-400 bg-cyan-950/50 shadow-md shadow-cyan-500/20"
                  : isKeyBeat
                  ? "border-slate-700 bg-slate-900 hover:border-cyan-800"
                  : "border-slate-800/80 bg-slate-950/40 hover:bg-slate-900/60"
              }`}
            >
              <span className={`text-xs font-mono font-bold ${isSelected ? "text-cyan-300" : "text-slate-300"}`}>
                D{d}
              </span>

              {/* Status dot */}
              <div className="mt-1 flex items-center justify-center">
                {d === 13 || d === 14 ? (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                ) : d === 10 || d === 12 ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                ) : d === 5 ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                ) : (
                  <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Beat Callout Banner */}
      {activeBeat && (
        <div className={`flex items-start gap-3 p-3 rounded-lg border text-xs ${activeBeat.color} transition-all`}>
          <div className="mt-0.5">{activeBeat.icon}</div>
          <div className="space-y-0.5">
            <span className="font-bold">{activeBeat.title}</span>
            <p className="text-slate-300 font-sans">{activeBeat.desc}</p>
          </div>
        </div>
      )}
    </div>
  );
};
