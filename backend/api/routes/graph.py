"""Project TRIDENT — Graph API Routes (Screen 2 Causal Graph).

Endpoints:
- GET /api/graph/causal: Returns minimal causal evidence subgraph payload for React Flow
- GET /api/graph/ego: Returns k-hop ego network for an actor
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query

from backend.api.manager import demo_manager
from backend.evidence.schemas import CausalSubgraphPayload
from backend.graph.schemas import ReactFlowGraph
from backend.graph.subgraph_extractor import TimeWindowExtractor

router = APIRouter(prefix="/api/graph", tags=["Graph"])


@router.get("/causal", response_model=CausalSubgraphPayload)
def get_causal_graph(day: Optional[int] = Query(default=None, ge=1, le=14)):
    """Returns the minimal causal evidence subgraph payload formatted for React Flow."""
    return demo_manager.get_causal_subgraph(day)


@router.get("/ego", response_model=ReactFlowGraph)
def get_ego_graph(
    actor_token: Optional[str] = Query(default=None),
    hops: int = Query(default=2, ge=1, le=3),
):
    """Returns k-hop ego network centered on actor."""
    token = actor_token or demo_manager.active_dataset.metadata.primary_actor_token
    extractor = TimeWindowExtractor(demo_manager.graph_builder)
    ego_builder = extractor.extract_ego_subgraph(seed_actor_token=token, hops=hops)
    return extractor.to_react_flow(ego_builder)
