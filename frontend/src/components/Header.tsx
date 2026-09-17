"use client";

import React from "react";
import { Shield, Activity, GitFork, Lock, AlertTriangle, Play, Pause, ChevronRight } from "lucide-react";
import { ScenarioDaySnapshot, ScenarioMetadata } from "@/lib/types";

interface HeaderProps {
  activeScreen: 1 | 2 | 3;
  setActiveScreen: (screen: 1 | 2 | 3) => void;
  selectedDay: number;
  setSelectedDay: (day: number) => void;
  scenarios: ScenarioMetadata[];
  activeScenario: string;
  onScenarioChange: (scenarioId: string) => void;
  currentSnapshot?: ScenarioDaySnapshot;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  setActiveScreen,
  selectedDay,
  setSelectedDay,
  scenarios,
  activeScenario,
  onScenarioChange,
  currentSnapshot,
  isPlaying,
  setIsPlaying,
}) => {
  const getTierBadge = () => {
    if (!currentSnapshot) return null;
    const tier = currentSnapshot.risk_tier;
    if (tier.includes("CRITICAL")) {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-rose-950/80 text-rose-400 border border-rose-600/50 glow-rose">TIER 4 CRITICAL</span>;
    }
    if (tier.includes("HIGH_RISK")) {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-950/80 text-amber-400 border border-amber-500/50 glow-amber">TIER 3 HIGH RISK</span>;
    }
    if (tier.includes("UNANCHORED")) {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-yellow-950/80 text-yellow-400 border border-yellow-500/40">TIER 2 EXPLORATION</span>;
    }
    return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-950/80 text-emerald-400 border border-emerald-500/40">TIER 1 CONTEXTUAL</span>;
  };

  const getCanaryBadge = () => {
    if (!currentSnapshot) return null;
    if (currentSnapshot.canary_state === "CONFIRMED") {
      return (
        <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-rose-500/20 text-rose-300 border border-rose-500/60 flex items-center gap-1.5 animate-pulse">
          <span className="w-2 h-2 rounded-full bg-rose-500"></span>
          CANARY TRIPPED (CONFIRMED)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-mono rounded bg-slate-800/80 text-slate-400 border border-slate-700 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
        CANARY ARMED (PROBABILISTIC)
      </span>
    );
  };

  return (
    <header className="border-b border-slate-800 bg-[#0c1220]/95 sticky top-0 z-50 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top brand row */}
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Shield className="w-5 h-5 text-black" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-black tracking-wider text-slate-100">TRIDENT</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">v1.0-SOC</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">Measured Today</span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Trust-Anchored Risk Intelligence, Drift & Evidence Network</p>
            </div>
          </div>

          {/* Scenario selector & simulation controls */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-lg px-2.5 py-1">
              <span className="text-xs text-slate-400 font-mono">Scenario:</span>
              <select
                value={activeScenario}
                onChange={(e) => onScenarioChange(e.target.value)}
                aria-label="Select Scenario"
                className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer font-medium"
              >
                {scenarios.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id} className="bg-slate-900 text-slate-200">
                    {s.title}
                  </option>
                ))}
              </select>
            </div>

            {getTierBadge()}
            {getCanaryBadge()}
          </div>
        </div>

        {/* Navigation row: 3 Screens + Interactive Day Scrubber */}
        <div className="flex items-center justify-between py-2 border-t border-slate-800/80">
          <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveScreen(1)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeScreen === 1
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Screen 1: Dual Timeline</span>
            </button>

            <button
              onClick={() => setActiveScreen(2)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeScreen === 2
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <GitFork className="w-3.5 h-3.5" />
              <span>Screen 2: Graph & Trajectory</span>
            </button>

            <button
              onClick={() => setActiveScreen(3)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeScreen === 3
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Screen 3: Privacy Vault</span>
            </button>
          </div>

          {/* Mini Scrubber in Header */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title={isPlaying ? "Pause 14-Day Simulation" : "Auto-Play 14-Day Demo"}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 text-amber-400" /> : <Play className="w-3.5 h-3.5 text-cyan-400" />}
            </button>

            <span className="text-xs font-mono text-slate-400">Day:</span>
            <div className="flex items-center gap-1">
              {Array.from({ length: 14 }, (_, i) => i + 1).map((d) => (
                <button
                  key={d}
                  onClick={() => setSelectedDay(d)}
                  className={`w-6 h-6 text-xs font-mono rounded flex items-center justify-center transition-all ${
                    selectedDay === d
                      ? "bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/30"
                      : d === 5 || d === 9 || d === 10 || d === 13 || d === 14
                      ? "bg-slate-800 text-cyan-300 border border-cyan-800/50 hover:bg-slate-700"
                      : "bg-slate-900/80 text-slate-400 hover:bg-slate-800"
                  }`}
                  title={
                    d === 5
                      ? "Beat 2: Benign Anomaly Suppressed"
                      : d === 9
                      ? "Beat 2: Silent Drift Begins"
                      : d === 10
                      ? "Beat 3: Fabricated Context Rejected"
                      : d === 13
                      ? "Beat 4: Simulated Canary Tripped"
                      : d === 14
                      ? "Beat 5: Critical Escalation & MITRE Dossier"
                      : `Day ${d}`
                  }
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
