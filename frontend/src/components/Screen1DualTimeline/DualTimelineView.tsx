"use client";

import React, { useEffect, useState } from "react";
import { Activity, Shield, TrendingUp, Lock, FileCheck, AlertTriangle } from "lucide-react";
import { CanonicalEvent, ScenarioDaySnapshot } from "@/lib/types";
import { TimelineChart } from "./TimelineChart";
import { DayScrubber } from "./DayScrubber";
import { DailyEventsDrawer } from "./DailyEventsDrawer";
import { api } from "@/lib/api";

interface DualTimelineViewProps {
  timeline: ScenarioDaySnapshot[];
  selectedDay: number;
  setSelectedDay: (day: number) => void;
}

export const DualTimelineView: React.FC<DualTimelineViewProps> = ({
  timeline,
  selectedDay,
  setSelectedDay,
}) => {
  const [events, setEvents] = useState<CanonicalEvent[]>([]);
  const currentSnapshot = timeline[selectedDay - 1] || timeline[timeline.length - 1];

  useEffect(() => {
    let isMounted = true;
    api.getTimelineEvents(selectedDay).then((evts) => {
      if (isMounted) setEvents(evts);
    });
    return () => {
      isMounted = false;
    };
  }, [selectedDay]);

  return (
    <div className="space-y-4">
      {/* 5 High-Level KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Subject Token */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono">Subject Token</span>
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="mt-2">
            <span className="text-sm font-bold font-mono text-cyan-300">Subject-Theta-482</span>
            <p className="text-[11px] text-slate-500">HMAC Pseudonymized</p>
          </div>
        </div>

        {/* CAS Score */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono">Context Authenticity</span>
            <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold font-mono text-slate-100">
                {currentSnapshot ? (currentSnapshot.context_authenticity_score * 100).toFixed(0) : 0}%
              </span>
              <span className="text-[10px] text-slate-400 font-mono">10-Signal CAS</span>
            </div>
            <p className="text-[11px] text-slate-500">
              {currentSnapshot && currentSnapshot.context_authenticity_score >= 0.7
                ? "Verified Organizational Anchor"
                : currentSnapshot && currentSnapshot.context_authenticity_score === 0
                ? "Zero Business Anchor"
                : "Fabricated Context Rejected"}
            </p>
          </div>
        </div>

        {/* Discount Factor */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono">Context Discount (δ)</span>
            <Shield className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold font-mono text-slate-100">
                {currentSnapshot ? currentSnapshot.discount_factor.toFixed(2) : "1.00"}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">δ ≥ 0.15 (Capped)</span>
            </div>
            <p className="text-[11px] text-slate-500">
              {currentSnapshot && currentSnapshot.discount_factor <= 0.4
                ? "78% Anomaly Attenuation"
                : "Residual Risk Baseline 15%"}
            </p>
          </div>
        </div>

        {/* CUSUM Cumulative Drift */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono">CUSUM Drift (S_t)</span>
            <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold font-mono text-purple-300">
                {currentSnapshot ? currentSnapshot.cusum_drift_score.toFixed(2) : "0.00"}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Slack k=0.15</span>
            </div>
            <p className="text-[11px] text-slate-500">
              {currentSnapshot && currentSnapshot.cusum_drift_score >= 4.0
                ? "CRITICAL Drift Trajectory"
                : currentSnapshot && currentSnapshot.cusum_drift_score >= 2.0
                ? "HIGH RISK Trajectory"
                : "Within Baseline Bounds"}
            </p>
          </div>
        </div>

        {/* Composite Risk Score */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono">Composite Risk</span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold font-mono text-rose-400">
                {currentSnapshot ? currentSnapshot.composite_risk.toFixed(1) : "0.0"}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">/ 100</span>
            </div>
            <p className="text-[11px] text-rose-300/80 font-medium">
              {currentSnapshot ? currentSnapshot.risk_tier.replace("TIER_", "Tier ").replace(/_/g, " ") : "Normal"}
            </p>
          </div>
        </div>
      </div>

      {/* Main Dual Timeline Chart */}
      <TimelineChart
        timeline={timeline}
        selectedDay={selectedDay}
        onSelectDay={setSelectedDay}
      />

      {/* 14-Day Scrubber */}
      <DayScrubber
        selectedDay={selectedDay}
        setSelectedDay={setSelectedDay}
        timeline={timeline}
      />

      {/* Telemetry Events Drawer */}
      <DailyEventsDrawer
        day={selectedDay}
        events={events}
      />
    </div>
  );
};
