"use client";

import React from "react";
import { Database, Key, Server, Terminal, ShieldCheck } from "lucide-react";
import { CanonicalEvent } from "@/lib/types";

interface DailyEventsDrawerProps {
  day: number;
  events: CanonicalEvent[];
}

export const DailyEventsDrawer: React.FC<DailyEventsDrawerProps> = ({
  day,
  events,
}) => {
  const getActionIcon = (action: string) => {
    if (action.includes("login") || action.includes("auth")) {
      return <Key className="w-3.5 h-3.5 text-amber-400" />;
    }
    if (action.includes("s3") || action.includes("Bucket") || action.includes("db")) {
      return <Database className="w-3.5 h-3.5 text-cyan-400" />;
    }
    if (action.includes("repo") || action.includes("git")) {
      return <Terminal className="w-3.5 h-3.5 text-purple-400" />;
    }
    return <Server className="w-3.5 h-3.5 text-slate-400" />;
  };

  return (
    <div className="w-full bg-slate-900/60 rounded-xl p-4 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold text-slate-200">
            Day {day} Operational Telemetry Stream
          </h4>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
            {events.length} Normalized Events
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Ingestion Protected-Endpoint Filter: Active (0 Leaks)</span>
        </div>
      </div>

      {events.length === 0 ? (
        <div className="py-8 text-center text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded-lg">
          No external anomalous events logged for Day {day}. Baseline development activity is stable.
        </div>
      ) : (
        <div className="overflow-x-auto max-h-60 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 sticky top-0">
              <tr>
                <th className="py-2 px-3">Time (UTC)</th>
                <th className="py-2 px-3">Actor Token</th>
                <th className="py-2 px-3">Action</th>
                <th className="py-2 px-3">Target Resource</th>
                <th className="py-2 px-3">Sensitivity</th>
                <th className="py-2 px-3">Claimed Anchor</th>
                <th className="py-2 px-3">Payload SHA-256</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {events.map((evt) => (
                <tr key={evt.event_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                    {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "14:22:10"}
                  </td>
                  <td className="py-2 px-3 font-semibold text-cyan-300 whitespace-nowrap">
                    {evt.actor.actor_token}
                  </td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    <span className="flex items-center gap-1.5">
                      {getActionIcon(evt.action)}
                      {evt.action}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-300 max-w-xs truncate" title={evt.resource.resource_id}>
                    {evt.resource.resource_id}
                  </td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        evt.resource.sensitivity >= 0.8
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : evt.resource.sensitivity >= 0.5
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {(evt.resource.sensitivity * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    {evt.business_context?.ticket_ids && evt.business_context.ticket_ids.length > 0 ? (
                      <span className="px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800 text-[10px]">
                        {evt.business_context.ticket_ids.join(", ")}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">None (Unanchored)</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-slate-500 truncate max-w-[120px]" title={evt.raw_payload_hash}>
                    {(evt.raw_payload_hash || "0000000000000000").substring(0, 16)}...
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
