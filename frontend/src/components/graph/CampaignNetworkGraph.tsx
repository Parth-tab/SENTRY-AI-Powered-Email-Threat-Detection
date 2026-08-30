import React, { useState, useEffect, useRef } from "react";
import { Network, Filter, ZoomIn, ZoomOut, RotateCcw, Info, AlertCircle, Layers, ShieldAlert, Globe } from "lucide-react";
import { fetchGlobalGraph } from "../../services/api";
import { GraphData, GraphNode, GraphLink } from "../../types";

const MAX_GRAPH_NODES = 300;

export const CampaignNetworkGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mode, setMode] = useState<"cluster" | "supernode" | "detailed">("cluster");
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>("");
  const [collapseSynthetic, setCollapseSynthetic] = useState<boolean>(true);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Load graph data based on mode & campaign filter
  useEffect(() => {
    setIsLoading(true);
    fetchGlobalGraph({
      campaignId: selectedCampaignId || undefined,
      mode: mode,
      maxNodes: MAX_GRAPH_NODES,
      collapseSynthetic: collapseSynthetic
    })
      .then((data) => {
        setGraphData(data);
        if (!selectedCampaignId && data.active_campaign_id && data.active_campaign_id !== "all") {
          setSelectedCampaignId(data.active_campaign_id);
        }
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, [mode, selectedCampaignId, collapseSynthetic]);

  // Canvas render step (incorporating Phase 1 data layer: supernodes, weighted edges, badges)
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

    // Phase 1 layout initialization: separate supernodes or distribute cluster
    const nodes = cappedNodes.map((n, i) => {
      const isSuper = n.type === "CampaignSupernode" || n.type === "Campaign";
      const baseRadius = isSuper ? 120 : (160 + (i % 3) * 45);
      const angle = (i / Math.max(cappedNodes.length, 1)) * 2 * Math.PI;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * baseRadius,
        y: height / 2 + Math.sin(angle) * baseRadius,
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

      // 1. Draw Links (with weighted width)
      links.forEach((link) => {
        if (!link.sourceNode || !link.targetNode) return;
        ctx.beginPath();
        ctx.moveTo(link.sourceNode.x, link.sourceNode.y);
        ctx.lineTo(link.targetNode.x, link.targetNode.y);
        
        const weight = link.weight || 1;
        ctx.lineWidth = Math.min(Math.max(1, weight * 0.4), 5);
        ctx.strokeStyle = weight > 1 ? "#52525B" : "#3F3F46";
        ctx.stroke();
      });

      // 2. Draw Nodes
      nodes.forEach((node) => {
        let radius = 8;
        let fill = "#A1A1AA";
        
        if (node.type === "CampaignSupernode") {
          radius = 14;
          fill = "#EC4899";
        } else if (node.type === "Campaign") {
          radius = 12;
          fill = "#EC4899";
        } else if (node.type === "Infrastructure") {
          radius = 10;
          fill = "#10B981";
        } else if (node.type === "BrandTarget") {
          radius = 10;
          fill = "#6366F1";
        } else if (node.type === "Email") {
          radius = 6;
          fill = "#FA7273";
        } else if (node.type === "Domain") {
          radius = 8;
          fill = "#38BDF8";
        } else if (node.type === "IPAddress") {
          radius = 8;
          fill = "#F59E0B";
        }

        // Draw outer glow for supernodes or high threat
        if (node.type === "CampaignSupernode" || node.threat_score && node.threat_score >= 0.8) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
          ctx.fillStyle = fill + "33";
          ctx.fill();
        }

        // Draw node body
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = fill;
        ctx.fill();
        ctx.strokeStyle = "#18181B";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw badge count if present
        if (node.badge_count && node.badge_count > 1) {
          ctx.beginPath();
          ctx.arc(node.x + radius - 2, node.y - radius + 2, 6, 0, 2 * Math.PI);
          ctx.fillStyle = "#F43F5E";
          ctx.fill();
          ctx.fillStyle = "#FFFFFF";
          ctx.font = "bold 8px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(Math.min(node.badge_count, 99)), node.x + radius - 2, node.y - radius + 2);
          ctx.textAlign = "left";
          ctx.textBaseline = "alphabetic";
        }

        // Label
        ctx.fillStyle = "#E4E4E7";
        ctx.font = node.type === "CampaignSupernode" ? "bold 11px sans-serif" : "10px monospace";
        ctx.fillText(node.label || node.id, node.x + radius + 4, node.y + 3);
      });

      // Simple physics decay
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
  const availableCampaigns = graphData?.available_campaigns || [];

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-[#27272A] gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 flex items-center space-x-2">
            <Network className="w-4 h-4 text-rose-500" />
            <span>Multi-Entity Campaign Knowledge Graph</span>
            {mode === "supernode" && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-pink-500/20 text-pink-300 border border-pink-500/40 font-mono">
                Supernodes Mode (Collapsed)
              </span>
            )}
            {mode === "cluster" && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono">
                Focused Cluster View
              </span>
            )}
          </h2>
          <p className="text-xs text-zinc-400">
            Multi-dimensional threat campaign correlation across Infrastructure, ASNs, Lookalike Domains, and Attack Vectors
          </p>
        </div>

        {/* Mode Selector & Campaign Dropdown */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Mode Switcher */}
          <div className="flex bg-[#121215] p-1 rounded-lg border border-[#27272A] text-xs">
            <button
              onClick={() => setMode("cluster")}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                mode === "cluster"
                  ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Cluster View
            </button>
            <button
              onClick={() => setMode("supernode")}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                mode === "supernode"
                  ? "bg-pink-500/20 text-pink-300 border border-pink-500/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              All Supernodes
            </button>
            <button
              onClick={() => setMode("detailed")}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                mode === "detailed"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Detailed (Capped)
            </button>
          </div>

          {/* Campaign Selector (Active in Cluster Mode) */}
          {mode === "cluster" && availableCampaigns.length > 0 && (
            <select
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              className="bg-[#121215] text-zinc-200 text-xs rounded-lg px-2.5 py-1.5 border border-[#27272A] focus:outline-none focus:border-rose-500 font-mono"
            >
              {availableCampaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.name.substring(0, 32)}... ({c.email_count} emails)
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {isCapped && mode === "detailed" && (
        <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>
            <strong>Diversity Cap Active (G-D8 / GRAPH-003):</strong> Displaying stratified top {MAX_GRAPH_NODES} entities preserving per-campaign diversity across {totalDbEntities.toLocaleString()} total DB records.
          </span>
        </div>
      )}

      {/* Graph Legend & Canvas Container */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs font-mono bg-[#121215] p-2.5 rounded-lg border border-[#27272A]">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#EC4899]" />
              <span className="text-zinc-300">Campaign Supernode</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#10B981]" />
              <span className="text-zinc-300">Infrastructure (ASN)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#6366F1]" />
              <span className="text-zinc-300">Targeted Brand</span>
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
          </div>

          <div className="text-[11px] text-zinc-400">
            Nodes: <span className="text-zinc-200 font-bold">{graphData?.nodes?.length || 0}</span> | Collapsed Edges: <span className="text-zinc-200 font-bold">{graphData?.links?.length || 0}</span>
          </div>
        </div>

        {/* Graph Canvas */}
        <div className="relative w-full h-[450px] bg-[#0E0E11] rounded-xl border border-[#27272A] flex items-center justify-center overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 bg-[#0E0E11]/70 backdrop-blur-xs flex items-center justify-center text-xs text-zinc-400 z-10">
              Correlating campaign graph...
            </div>
          )}
          <canvas
            ref={canvasRef}
            width={900}
            height={500}
            className="w-full h-full cursor-pointer"
          />

          {/* Node Inspection Drawer */}
          {selectedNode && (
            <div className="absolute top-4 right-4 w-80 bg-[#18181B]/95 backdrop-blur border border-[#27272A] p-4 rounded-xl shadow-2xl text-xs space-y-2 font-mono z-20">
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
