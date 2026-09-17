"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";

interface DriftAttributionChartProps {
  day: number;
}

export const DriftAttributionChart: React.FC<DriftAttributionChartProps> = ({ day }) => {
  // Dimension z-scores scale up with day progression
  const scale = Math.min(1.0, day / 14);
  const data = [
    { dimension: "Event Volume", zScore: parseFloat((1.2 + 2.4 * scale).toFixed(1)), threshold: 2.0 },
    { dimension: "Sensitivity", zScore: parseFloat((1.0 + 2.8 * scale).toFixed(1)), threshold: 2.0 },
    { dimension: "Discovery", zScore: parseFloat((0.8 + 2.2 * scale).toFixed(1)), threshold: 2.0 },
    { dimension: "Off-Hours", zScore: parseFloat((0.4 + 1.9 * scale).toFixed(1)), threshold: 2.0 },
    { dimension: "Privilege", zScore: parseFloat((0.9 + 2.5 * scale).toFixed(1)), threshold: 2.0 },
    { dimension: "Boundary Entropy", zScore: parseFloat((1.1 + 2.7 * scale).toFixed(1)), threshold: 2.0 },
  ];

  return (
    <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold font-mono text-slate-200 uppercase">
            6-Dimension Drift Attribution (z-Score Deviation)
          </h4>
          <p className="text-[11px] text-slate-400 font-sans">
            Comparing Day {day} feature vector against 90-day slow baseline and peer cohort variance.
          </p>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-purple-300 border border-purple-800">
          Threshold: 2.0σ
        </span>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 20, right: 30, top: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" domain={[0, 5]} stroke="#64748b" tick={{ fontSize: 10, fill: "#94a3b8" }} />
            <YAxis
              type="category"
              dataKey="dimension"
              stroke="#64748b"
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              width={110}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-slate-950 border border-slate-700 rounded p-2 text-xs font-mono">
                    <p className="font-bold text-slate-200">{d.dimension}</p>
                    <p className="text-purple-400">Deviation: +{d.zScore}σ</p>
                    <p className="text-[10px] text-slate-400">
                      {d.zScore >= 2.0 ? "CRITICAL: Elevated past 2.0σ threshold" : "Within normal baseline bounds"}
                    </p>
                  </div>
                );
              }}
            />
            <ReferenceLine x={2.0} stroke="#f59e0b" strokeDasharray="3 3" />
            <Bar dataKey="zScore" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.zScore >= 3.0 ? "#f43f5e" : entry.zScore >= 2.0 ? "#f59e0b" : "#3b82f6"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
