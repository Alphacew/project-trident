"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { ScenarioDaySnapshot } from "@/lib/types";

interface TimelineChartProps {
  timeline: ScenarioDaySnapshot[];
  selectedDay: number;
  onSelectDay: (day: number) => void;
}

export const TimelineChart: React.FC<TimelineChartProps> = ({
  timeline,
  selectedDay,
  onSelectDay,
}) => {
  const chartData = timeline.map((snap) => ({
    day: `Day ${snap.day}`,
    dayNum: snap.day,
    rawAnomaly: snap.raw_anomaly_score,
    attenuatedRisk: snap.composite_risk,
    cusumDrift: parseFloat(snap.cusum_drift_score.toFixed(2)),
    casScore: snap.context_authenticity_score,
    discountFactor: snap.discount_factor,
    riskTier: snap.risk_tier,
  }));

  return (
    <div className="w-full h-80 bg-slate-900/60 rounded-xl p-4 border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-4">
          <h3 className="text-sm font-semibold text-slate-200">
            Dual Risk Trajectory & Recursive CUSUM Drift
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            Invariant 4: Attenuation Capped at 85% (Residual Risk ≥ 15%)
          </span>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 border-b-2 border-dashed border-rose-400"></span>
            <span className="text-slate-400">Raw Anomaly (R_raw)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-cyan-400 rounded-full"></span>
            <span className="text-cyan-300">Context-Attenuated Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-purple-400 rounded-full"></span>
            <span className="text-purple-300">Cumulative Drift (S_t)</span>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            onClick={(e) => {
              if (e && e.activePayload && e.activePayload[0]) {
                const dayNum = e.activePayload[0].payload.dayNum;
                if (dayNum) onSelectDay(dayNum);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis
              yAxisId="left"
              stroke="#64748b"
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              label={{ value: "Risk Score / 100", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 10 }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 6]}
              stroke="#a855f7"
              tick={{ fontSize: 11, fill: "#c084fc" }}
              label={{ value: "CUSUM S_t", angle: 90, position: "insideRight", fill: "#c084fc", fontSize: 10 }}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-slate-950 border border-slate-700 rounded-lg p-3 shadow-xl text-xs font-mono space-y-1">
                    <p className="font-bold text-slate-100 border-b border-slate-800 pb-1">{d.day}</p>
                    <p className="text-rose-400">Raw Anomaly: {d.rawAnomaly.toFixed(1)}</p>
                    <p className="text-cyan-400 font-semibold">Attenuated Risk: {d.attenuatedRisk.toFixed(1)} / 100</p>
                    <p className="text-purple-400">CUSUM Drift: {d.cusumDrift}</p>
                    <div className="pt-1 border-t border-slate-800/80 text-[11px] text-slate-400">
                      <p>Context CAS: {(d.casScore * 100).toFixed(0)}%</p>
                      <p>Discount Factor (δ): {d.discountFactor.toFixed(2)}</p>
                    </div>
                  </div>
                );
              }}
            />

            {/* Threshold reference lines */}
            <ReferenceLine yAxisId="right" y={0.8} stroke="#10b981" strokeDasharray="4 4" label={{ value: "Stable τ=0.8", fill: "#10b981", fontSize: 9 }} />
            <ReferenceLine yAxisId="right" y={2.0} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "High-Risk τ=2.0", fill: "#f59e0b", fontSize: 9 }} />
            <ReferenceLine yAxisId="right" y={4.0} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: "Critical τ=4.0", fill: "#f43f5e", fontSize: 9 }} />

            {/* Active Selected Day reference */}
            <ReferenceLine x={`Day ${selectedDay}`} stroke="#06b6d4" strokeWidth={2} />

            {/* Lines */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="rawAnomaly"
              stroke="#f43f5e"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              dot={false}
              name="Raw Anomaly"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="attenuatedRisk"
              stroke="#06b6d4"
              strokeWidth={2.5}
              dot={{ r: 3, fill: "#06b6d4" }}
              activeDot={{ r: 6, fill: "#22d3ee" }}
              name="Attenuated Risk"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cusumDrift"
              stroke="#a855f7"
              strokeWidth={2}
              dot={{ r: 3, fill: "#a855f7" }}
              name="CUSUM Drift"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
