"use client";

import React, { useEffect, useState } from "react";
import { FlowGraph } from "./FlowGraph";
import { CanaryCard } from "./CanaryCard";
import { ForensicDossierCard } from "./ForensicDossierCard";
import { DriftAttributionChart } from "./DriftAttributionChart";
import { CanaryDecoy, CausalEdge, CausalNode, ForensicDossier } from "@/lib/types";
import { api } from "@/lib/api";
import { MOCK_CANARY_STATUS, MOCK_CAUSAL_EDGES, MOCK_CAUSAL_NODES, MOCK_FORENSIC_DOSSIER } from "@/lib/mockData";

interface CausalGraphViewProps {
  selectedDay: number;
}

export const CausalGraphView: React.FC<CausalGraphViewProps> = ({ selectedDay }) => {
  const [nodes, setNodes] = useState<CausalNode[]>(MOCK_CAUSAL_NODES);
  const [edges, setEdges] = useState<CausalEdge[]>(MOCK_CAUSAL_EDGES);
  const [canaryStatus, setCanaryStatus] = useState<CanaryDecoy>(MOCK_CANARY_STATUS);
  const [dossier, setDossier] = useState<ForensicDossier>(MOCK_FORENSIC_DOSSIER);
  const [isTripping, setIsTripping] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    api.getCausalGraph(selectedDay).then((data) => {
      if (isMounted) {
        setNodes(data.nodes);
        setEdges(data.edges);
      }
    });

    api.getCanaryStatus().then((status) => {
      if (isMounted) {
        // If day < 13, simulate armed not tripped unless user triggered
        if (selectedDay < 13) {
          setCanaryStatus({
            ...status,
            is_tripped: false,
            confirmation_state: "PROBABILISTIC",
          });
        } else {
          setCanaryStatus(status);
        }
      }
    });

    api.getForensicDossier(selectedDay).then((dos) => {
      if (isMounted) setDossier(dos);
    });

    return () => {
      isMounted = false;
    };
  }, [selectedDay]);

  const handleTripCanary = async () => {
    setIsTripping(true);
    try {
      const tripped = await api.triggerCanaryTrip();
      setCanaryStatus(tripped);

      // Refresh graph and dossier to reflect confirmed trip
      const graphData = await api.getCausalGraph(selectedDay);
      setNodes(graphData.nodes);
      setEdges(graphData.edges);

      const updatedDossier = await api.getForensicDossier(selectedDay);
      setDossier(updatedDossier);
    } finally {
      setIsTripping(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top row: React Flow DAG + Simulated Canary Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <FlowGraph
            nodes={nodes}
            edges={edges}
            canaryTripped={canaryStatus.is_tripped}
          />
        </div>

        <div className="space-y-4">
          <CanaryCard
            canaryStatus={canaryStatus}
            onTripCanary={handleTripCanary}
            isTripping={isTripping}
          />

          <DriftAttributionChart day={selectedDay} />
        </div>
      </div>

      {/* Bottom row: Structured Forensic Dossier */}
      <ForensicDossierCard dossier={dossier} />
    </div>
  );
};
