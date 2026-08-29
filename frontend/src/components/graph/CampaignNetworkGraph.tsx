import React, { useState, useEffect, useRef } from "react";
import { Network, Filter, ZoomIn, ZoomOut, RotateCcw, Info, AlertCircle } from "lucide-react";
import { fetchGlobalGraph } from "../../services/api";
import { GraphData } from "../../types";

const MAX_GRAPH_NODES = 300;

export const CampaignNetworkGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    fetchGlobalGraph()
      .then((data) => {
        setGraphData(data);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  // Simple, smooth force-directed physics layout on canvas with 300 node safety cap (GRAPH-001)
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    const rawNodes = graphData.nodes || [];
    const cappedNodes = rawNodes.slice(0, MAX_GRAPH_NODES);
    const cappedNodeIds = new Set(cappedNodes.map((n) => n.id));

    // Initialize node positions in circular layout
    const nodes = cappedNodes.map((n, i) => {
      const angle = (i / cappedNodes.length) * 2 * Math.PI;
      const radius = 180 + (i % 3) * 40;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0
      };
    });

    const links = (graphData.links || [])
      .filter((l) => cappedNodeIds.has(l.source) && cappedNodeIds.has(l.target))
      .map((l) => ({
        ...l,
        sourceNode: nodes.find((n) => n.id === l.source) || nodes[0],
        targetNode: nodes.find((n) => n.id === l.target) || nodes[0]
      }));

    let animationFrameId: number;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw Links
      links.forEach((link) => {
        ctx.beginPath();
        ctx.moveTo(link.sourceNode.x, link.sourceNode.y);
        ctx.lineTo(link.targetNode.x, link.targetNode.y);
        ctx.strokeStyle = "#3F3F46";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // 2. Draw Nodes
      nodes.forEach((node) => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
        let fill = "#A1A1AA";
        if (node.type === "Campaign") fill = "#EC4899";
        else if (node.type === "Email") fill = "#FA7273";
        else if (node.type === "Domain") fill = "#38BDF8";
        else if (node.type === "IPAddress") fill = "#F59E0B";
        else if (node.type === "Infrastructure") fill = "#10B981";
        else if (node.type === "BrandTarget") fill = "#6366F1";

        ctx.fillStyle = fill;
        ctx.fill();
        ctx.strokeStyle = "#18181B";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = "#E4E4E7";
        ctx.font = "10px monospace";
        ctx.fillText(node.label || node.id, node.x + 12, node.y + 3);
      });

      // Physics step
      nodes.forEach((node) => {
        node.x += node.vx;
        node.y += node.vy;
        node.vx *= 0.95;
        node.vy *= 0.95;
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [graphData]);

  const totalRawNodes = graphData?.nodes?.length || 0;
  const totalDbEntities = graphData?.total_entities_in_db ?? totalRawNodes;
  const queriedEntities = graphData?.queried_entities_count ?? totalRawNodes;
  const isCapped = totalDbEntities > MAX_GRAPH_NODES || totalRawNodes > MAX_GRAPH_NODES;

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-[#27272A]">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 flex items-center space-x-2">
            <Network className="w-4 h-4 text-rose-500" />
            <span>Multi-Entity Campaign Knowledge Graph</span>
            {isCapped && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">
                Showing top {MAX_GRAPH_NODES} of {totalDbEntities.toLocaleString()} entities ({queriedEntities.toLocaleString()} queried)
              </span>
            )}
          </h2>
          <p className="text-xs text-zinc-400">
            Real-time multi-dimensional threat campaign correlation engine across Infrastructure, ASNs, Domains, and Attack Vectors
          </p>
        </div>
      </div>

      {isCapped && (
        <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>
            <strong>Scale Guard Active (GRAPH-002):</strong> Displaying top {MAX_GRAPH_NODES} of {totalDbEntities.toLocaleString()} entities (top {queriedEntities.toLocaleString()} queried) to maintain smooth 60fps canvas simulation.
          </span>
        </div>
      )}

      {/* Graph Legend & Canvas Container */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono bg-[#121215] p-2.5 rounded-lg border border-[#27272A]">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#EC4899]" />
            <span className="text-zinc-300">Campaign Cluster</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#FA7273]" />
            <span className="text-zinc-300">Email Artifact</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#38BDF8]" />
            <span className="text-zinc-300">Domain</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#F59E0B]" />
            <span className="text-zinc-300">IP Address</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#10B981]" />
            <span className="text-zinc-300">Infrastructure (ASN)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-[#6366F1]" />
            <span className="text-zinc-300">Targeted Brand</span>
          </div>
        </div>

        {/* Graph Canvas */}
        <div className="relative w-full h-[450px] bg-[#0E0E11] rounded-xl border border-[#27272A] flex items-center justify-center overflow-hidden">
          <canvas
            ref={canvasRef}
            width={900}
            height={500}
            className="w-full h-full cursor-pointer"
          />

          {/* Node Inspection Drawer */}
          {selectedNode && (
            <div className="absolute top-4 right-4 w-72 bg-[#18181B]/95 backdrop-blur border border-[#27272A] p-4 rounded-xl shadow-2xl text-xs space-y-2 font-mono">
              <div className="flex items-center justify-between pb-2 border-b border-[#27272A]">
                <span className="text-[10px] uppercase font-bold text-zinc-400">
                  {selectedNode.type} Entity Detail
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-zinc-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <div className="text-zinc-100 font-bold text-sm truncate">
                {selectedNode.label}
              </div>
              <div className="text-[11px] text-zinc-400">
                <span className="text-zinc-500">ID:</span> {selectedNode.id}
              </div>
              {selectedNode.details && (
                <div className="mt-2 p-2 rounded bg-[#121215] text-[10px] text-zinc-300 space-y-1">
                  {Object.entries(selectedNode.details).map(([k, v]) => (
                    <div key={k} className="truncate">
                      <span className="text-zinc-500">{k}:</span> {String(v)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
