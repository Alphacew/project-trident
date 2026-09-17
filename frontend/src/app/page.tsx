"use client";

import React, { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { DualTimelineView } from "@/components/Screen1DualTimeline/DualTimelineView";
import { CausalGraphView } from "@/components/Screen2CausalGraph/CausalGraphView";
import { PrivacyVaultView } from "@/components/Screen3PrivacyVault/PrivacyVaultView";
import { ScenarioDaySnapshot, ScenarioMetadata } from "@/lib/types";
import { api } from "@/lib/api";
import { MOCK_SCENARIOS, MOCK_TIMELINE_SNAPSHOTS } from "@/lib/mockData";
import { ShieldCheck, Info } from "lucide-react";

export default function SOCConsolePage() {
  const [activeScreen, setActiveScreen] = useState<1 | 2 | 3>(1);
  const [selectedDay, setSelectedDay] = useState<number>(14);
  const [scenarios, setScenarios] = useState<ScenarioMetadata[]>(MOCK_SCENARIOS);
  const [activeScenario, setActiveScenario] = useState<string>("MASTER_DEMO");
  const [timeline, setTimeline] = useState<ScenarioDaySnapshot[]>(MOCK_TIMELINE_SNAPSHOTS);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Load scenarios on mount
  useEffect(() => {
    api.getScenarios().then(setScenarios);
    api.getTimeline().then(setTimeline);
  }, []);

  // Handle scenario switch
  const handleScenarioChange = async (scenarioId: string) => {
    setActiveScenario(scenarioId);
    const updatedTimeline = await api.switchScenario(scenarioId);
    setTimeline(updatedTimeline);
    setSelectedDay(14); // Jump to final day
  };

  // Auto-play timer stepping through days 1 to 14
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setSelectedDay((prev) => (prev >= 14 ? 1 : prev + 1));
    }, 2500);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const currentSnapshot = timeline[selectedDay - 1] || timeline[timeline.length - 1];

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Top Global Header & Navigation */}
      <Header
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        selectedDay={selectedDay}
        setSelectedDay={setSelectedDay}
        scenarios={scenarios}
        activeScenario={activeScenario}
        onScenarioChange={handleScenarioChange}
        currentSnapshot={currentSnapshot}
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
      />

      {/* Main Workspace View */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5">
        {activeScreen === 1 && (
          <DualTimelineView
            timeline={timeline}
            selectedDay={selectedDay}
            setSelectedDay={setSelectedDay}
          />
        )}

        {activeScreen === 2 && (
          <CausalGraphView selectedDay={selectedDay} />
        )}

        {activeScreen === 3 && (
          <PrivacyVaultView />
        )}
      </main>

      {/* Footer with Claim Ledger & Invariants */}
      <footer className="border-t border-slate-800/80 bg-[#090e1a] py-4 text-xs font-mono text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-bold text-slate-200">PROJECT TRIDENT</span>
            <span>•</span>
            <span className="text-slate-400">Trust the context. Track the trajectory. Prove the threat.</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              Claim Ledger: <strong className="text-cyan-400">Measured Today</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              Decoys: <strong className="text-rose-400">Simulated Canary</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              Custody: <strong className="text-purple-400">Shamir 2-of-3</strong>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
