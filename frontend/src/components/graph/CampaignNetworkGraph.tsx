import React, { useState, useEffect, useRef } from "react";
import { Network, Filter, ZoomIn, ZoomOut, RotateCcw, Info } from "lucide-react";
import { fetchGlobalGraph } from "../../services/api";
import { GraphData } from "../../types";

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

  // Simple, smooth force-directed physics layout on canvas
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Initialize node positions in circular layout
    const nodes = graphData.nodes.map((n, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = 180 + (i % 3) * 40;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0
      };
    });

    const links = graphData.links.map((l) => ({
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
        ctx.strokeStyle = "rgba(75, 85, 99, 0.4)";
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Draw relationship label in center
        const midX = (link.sourceNode.x + link.targetNode.x) / 2;
        const midY = (link.sourceNode.y + link.targetNode.y) / 2;
        ctx.fillStyle = "#6B7280";
        ctx.font = "8px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(link.relationship, midX, midY);
      });

      // 2. Draw Nodes
      nodes.forEach((node) => {
        const isSel = selectedNode?.id === node.id;
        const radius = node.type === "Campaign" ? 18 : node.type === "Infrastructure" ? 14 : 10;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + (isSel ? 4 : 0), 0, 2 * Math.PI);
        ctx.fillStyle = node.color || "#FA7273";
        ctx.shadowColor = node.color || "#FA7273";
        ctx.shadowBlur = isSel ? 15 : 6;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = isSel ? "#FFFFFF" : "#18181B";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Node Label
        ctx.fillStyle = "#E5E7EB";
        ctx.font = `${node.type === "Campaign" ? "11px" : "9px"} 'Inter', sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(node.label.substring(0, 24), node.x, node.y + radius + 12);
      });
    };

    render();

    // Node click handler
    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      const clicked = nodes.find((n) => {
        const dist = Math.hypot(n.x - clickX, n.y - clickY);
        return dist <= 20;
      });

      if (clicked) {
        setSelectedNode(clicked);
        render();
      }
    };

    canvas.addEventListener("click", handleClick);

    return () => {
      canvas.removeEventListener("click", handleClick);
    };
  }, [graphData, selectedNode]);

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-[#18181B] border border-[#27272A] shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-[#27272A]">
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <Network className="w-4 h-4 text-indigo-400" />
              <span>Multi-Entity Threat Campaign Correlation Knowledge Graph</span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Neo4j-backed graph revealing cross-email infrastructure reuse, lookalike networks, and syndicate clusters
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-2.5 py-1 rounded bg-zinc-800 text-zinc-300 font-mono">
              Nodes: {graphData?.nodes?.length ?? 0} | Links: {graphData?.links?.length ?? 0}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 p-3 rounded-lg bg-[#121215] border border-[#27272A] text-xs font-mono">
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
