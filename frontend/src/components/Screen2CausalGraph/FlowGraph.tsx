"use client";

import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { User, Key, Database, FolderGit2, HardDrive, ShieldAlert, Sparkles } from "lucide-react";
import { CausalEdge, CausalNode } from "@/lib/types";

interface FlowGraphProps {
  nodes: CausalNode[];
  edges: CausalEdge[];
  onNodeClick?: (nodeId: string) => void;
  canaryTripped: boolean;
}

// Custom Node Components
const CustomActorNode = ({ data }: { data: any }) => (
  <div className="px-4 py-3 rounded-xl bg-slate-900 border-2 border-cyan-400/80 shadow-lg shadow-cyan-500/20 text-slate-100 flex items-center gap-3 min-w-[200px]">
    <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center">
      <User className="w-4 h-4 text-cyan-300" />
    </div>
    <div>
      <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 block font-bold">Investigated Actor</span>
      <span className="text-xs font-mono font-semibold">{data.label}</span>
    </div>
  </div>
);

const CustomEntityNode = ({ data }: { data: any }) => {
  const getIcon = () => {
    if (data.category === "CREDENTIAL") return <Key className="w-4 h-4 text-amber-400" />;
    if (data.category === "DATABASE") return <Database className="w-4 h-4 text-rose-400" />;
    if (data.category === "DISCOVERY") return <FolderGit2 className="w-4 h-4 text-purple-400" />;
    return <HardDrive className="w-4 h-4 text-blue-400" />;
  };

  const getBorderColor = () => {
    if (data.sensitivity >= 0.9) return "border-rose-500/80 shadow-rose-500/20";
    if (data.sensitivity >= 0.7) return "border-amber-500/80 shadow-amber-500/20";
    return "border-slate-700 shadow-slate-900/50";
  };

  return (
    <div className={`px-4 py-3 rounded-xl bg-slate-900/90 border ${getBorderColor()} shadow-md text-slate-100 flex items-center gap-3 min-w-[210px]`}>
      <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center">
        {getIcon()}
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400 block uppercase">{data.category}</span>
          <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-300 font-mono">
            {(data.sensitivity * 100).toFixed(0)}% Sens
          </span>
        </div>
        <span className="text-xs font-mono font-medium truncate block max-w-[150px]" title={data.label}>
          {data.label}
        </span>
      </div>
    </div>
  );
};

const CustomCanaryNode = ({ data }: { data: any }) => {
  const isTripped = data.isTripped;
  return (
    <div
      className={`px-4 py-3 rounded-xl bg-slate-900 border-2 ${
        isTripped
          ? "border-rose-500 shadow-xl shadow-rose-600/40 glow-rose animate-pulse"
          : "border-cyan-400/60 shadow-lg shadow-cyan-500/20"
      } text-slate-100 flex items-center gap-3 min-w-[230px]`}
    >
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isTripped ? "bg-rose-500/20 text-rose-300" : "bg-cyan-500/20 text-cyan-300"}`}>
        <ShieldAlert className="w-4 h-4" />
      </div>
      <div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-400">
            {isTripped ? "CANARY TRIPPED (CONFIRMED)" : "SIMULATED CANARY"}
          </span>
        </div>
        <span className="text-xs font-mono font-semibold truncate block max-w-[170px]" title={data.label}>
          {data.label}
        </span>
      </div>
    </div>
  );
};

export const FlowGraph: React.FC<FlowGraphProps> = ({
  nodes: rawNodes,
  edges: rawEdges,
  canaryTripped,
}) => {
  const nodeTypes = useMemo(
    () => ({
      customActor: CustomActorNode,
      customEntity: CustomEntityNode,
      customCanary: CustomCanaryNode,
    }),
    []
  );

  // Position nodes logically in a DAG left-to-right
  const layoutPositions: Record<string, { x: number; y: number }> = {
    "node-actor": { x: 50, y: 150 },
    "node-cred": { x: 320, y: 60 },
    "node-repo": { x: 590, y: 60 },
    "node-db": { x: 320, y: 240 },
    "node-staging": { x: 590, y: 240 },
    "node-canary": { x: 860, y: 150 },
  };

  const rfNodes: Node[] = useMemo(
    () =>
      rawNodes.map((n) => ({
        id: n.id,
        type: n.category === "ACTOR" ? "customActor" : n.category === "CANARY" ? "customCanary" : "customEntity",
        position: layoutPositions[n.id] || { x: 100, y: 100 },
        data: {
          label: n.label,
          category: n.category,
          sensitivity: n.sensitivity,
          isTripped: n.category === "CANARY" ? canaryTripped : false,
        },
      })),
    [rawNodes, canaryTripped]
  );

  const rfEdges: Edge[] = useMemo(
    () =>
      rawEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: e.is_canary_trip ? canaryTripped : true,
        label: e.edge_type,
        labelStyle: { fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" },
        labelBgStyle: { fill: "#0f172a", fillOpacity: 0.8 },
        style: {
          stroke: e.is_canary_trip ? (canaryTripped ? "#f43f5e" : "#06b6d4") : e.sensitivity >= 0.8 ? "#f59e0b" : "#64748b",
          strokeWidth: e.is_canary_trip && canaryTripped ? 3 : 1.5,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: e.is_canary_trip && canaryTripped ? "#f43f5e" : "#64748b",
        },
      })),
    [rawEdges, canaryTripped]
  );

  return (
    <div className="w-full h-[440px] bg-[#070b14] rounded-xl border border-slate-800 relative overflow-hidden">
      <div className="absolute top-3 left-4 z-10 flex items-center gap-2 pointer-events-none">
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900/90 text-cyan-300 border border-slate-700">
          React Flow Causal DAG
        </span>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-400 border border-slate-700">
          Pruned Minimal Evidence Subgraph
        </span>
      </div>

      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
        className="text-xs"
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="bg-slate-900 border-slate-700 text-slate-300 fill-slate-300" />
      </ReactFlow>
    </div>
  );
};
