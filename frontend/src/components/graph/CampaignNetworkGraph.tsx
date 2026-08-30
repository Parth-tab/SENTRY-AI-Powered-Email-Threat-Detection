import React, { useState, useEffect, useRef, useCallback } from "react";
import { Network, Filter, ZoomIn, ZoomOut, RotateCcw, Info, AlertCircle, Layers, ShieldAlert, Globe, Activity } from "lucide-react";
import { fetchGlobalGraph } from "../../services/api";
import { GraphData, GraphNode, GraphLink } from "../../types";
import { GraphSimulation, SimNode, SimLink, computeConvexHull, GraphMetrics } from "./graphPhysics";

const MAX_GRAPH_NODES = 300;

declare global {
  interface Window {
    __graphMetrics?: GraphMetrics;
  }
}

export const CampaignNetworkGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<SimNode | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mode, setMode] = useState<"cluster" | "supernode" | "detailed">("cluster");
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>("");
  const [collapseSynthetic, setCollapseSynthetic] = useState<boolean>(true);
  const [metrics, setMetrics] = useState<GraphMetrics | null>(null);
  const [showHulls, setShowHulls] = useState<boolean>(true);
  
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const simRef = useRef<GraphSimulation | null>(null);

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

  // Main canvas animation and force physics simulation loop
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Initialize deterministic simulation
    const sim = new GraphSimulation(width, height, mode, 42);
    sim.initData(graphData.nodes || [], graphData.links || [], MAX_GRAPH_NODES);
    simRef.current = sim;

    let animationFrameId: number;

    const render = () => {
      // 1. Tick Physics
      sim.tick();

      // 2. Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Connected neighborhood for hovered node
      const hoveredId = hoveredNode?.id;
      const neighborNodeIds = new Set<string>();
      const neighborLinkKeys = new Set<string>();

      if (hoveredId) {
        neighborNodeIds.add(hoveredId);
        sim.links.forEach((l) => {
          if (l.source === hoveredId) {
            neighborNodeIds.add(l.target);
            neighborLinkKeys.add(`${l.source}->${l.target}`);
          } else if (l.target === hoveredId) {
            neighborNodeIds.add(l.source);
            neighborLinkKeys.add(`${l.source}->${l.target}`);
          }
        });
      }

      // 3. Draw Convex Hulls for campaign clusters
      if (showHulls && mode !== "supernode") {
        const clusterMap = new Map<string, Array<{ x: number; y: number }>>();
        sim.nodes.forEach((n) => {
          const cid = n.clusterId || (n.type === "Campaign" ? n.id : "default");
          if (!clusterMap.has(cid)) clusterMap.set(cid, []);
          clusterMap.get(cid)!.push({ x: n.x, y: n.y });
        });

        clusterMap.forEach((points, cid) => {
          if (points.length >= 3) {
            const hull = computeConvexHull(points);
            if (hull.length >= 3) {
              ctx.beginPath();
              ctx.moveTo(hull[0].x, hull[0].y);
              for (let i = 1; i < hull.length; i++) {
                ctx.lineTo(hull[i].x, hull[i].y);
              }
              ctx.closePath();
              ctx.fillStyle = "rgba(236, 72, 153, 0.04)";
              ctx.fill();
              ctx.strokeStyle = "rgba(236, 72, 153, 0.18)";
              ctx.lineWidth = 1.5;
              ctx.setLineDash([4, 4]);
              ctx.stroke();
              ctx.setLineDash([]);
            }
          }
        });
      }

      // 4. Draw Links (Curved Quadratic Bézier lines with alpha)
      sim.links.forEach((link) => {
        const u = link.sourceNode;
        const v = link.targetNode;
        if (!u || !v) return;

        const isHighlighted = !hoveredId || neighborLinkKeys.has(`${link.source}->${link.target}`);
        const alpha = isHighlighted ? (hoveredId ? 0.9 : 0.4) : 0.08;
        const weight = link.weight || 1;

        // Quadratic curve midpoint
        const mx = (u.x + v.x) / 2 + (u.y - v.y) * 0.08;
        const my = (u.y + v.y) / 2 + (v.x - u.x) * 0.08;

        ctx.beginPath();
        ctx.moveTo(u.x, u.y);
        ctx.quadraticCurveTo(mx, my, v.x, v.y);
        
        ctx.lineWidth = isHighlighted ? Math.min(Math.max(1, weight * 0.4), 5) : 0.8;
        ctx.strokeStyle = isHighlighted
          ? (weight > 1 ? `rgba(161, 161, 170, ${alpha})` : `rgba(82, 82, 91, ${alpha})`)
          : "rgba(39, 39, 42, 0.2)";
        ctx.stroke();
      });

      // 5. Draw Nodes
      sim.nodes.forEach((node) => {
        const isHovered = hoveredId === node.id;
        const isNeighbor = hoveredId ? neighborNodeIds.has(node.id) : true;
        const isHighPriorityHub =
          node.type === "CampaignSupernode" ||
          node.type === "Campaign" ||
          node.type === "Infrastructure" ||
          node.type === "BrandTarget";

        let fill = node.color || "#A1A1AA";
        const radius = isHovered ? node.radius + 3 : node.radius;

        // Draw outer glow for supernodes / high threat
        if (node.type === "CampaignSupernode" || (node.threat_score && node.threat_score >= 0.8)) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + (isHovered ? 6 : 4), 0, 2 * Math.PI);
          ctx.fillStyle = fill + (isNeighbor ? "33" : "0A");
          ctx.fill();
        }

        // Draw node body
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = isNeighbor ? fill : fill + "30";
        ctx.fill();
        ctx.strokeStyle = isHovered ? "#FFFFFF" : "#18181B";
        ctx.lineWidth = isHovered ? 2.5 : 1.5;
        ctx.stroke();

        // Draw badge count if present
        if (node.badge_count && node.badge_count > 1) {
          ctx.beginPath();
          ctx.arc(node.x + radius - 2, node.y - radius + 2, 6, 0, 2 * Math.PI);
          ctx.fillStyle = isNeighbor ? "#F43F5E" : "#F43F5E40";
          ctx.fill();
          ctx.fillStyle = "#FFFFFF";
          ctx.font = "bold 8px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(Math.min(node.badge_count, 99)), node.x + radius - 2, node.y - radius + 2);
          ctx.textAlign = "left";
          ctx.textBaseline = "alphabetic";
        }

        // Draw Text Label (only show for high-priority hubs or when hovered / 1-hop neighbor)
        const showLabel = isHovered || (hoveredId ? isNeighbor : isHighPriorityHub);
        if (showLabel) {
          ctx.fillStyle = isHovered || isHighPriorityHub ? "#F4F4F5" : "#A1A1AA";
          ctx.font = node.type === "CampaignSupernode" ? "bold 11px sans-serif" : "10px monospace";
          ctx.fillText(node.label || node.id, node.x + radius + 4, node.y + 3);
        }
      });

      // Update Legibility Metrics Hook (window.__graphMetrics)
      const currentMetrics = sim.getMetrics(selectedCampaignId, 42);
      window.__graphMetrics = currentMetrics;

      if (sim.alpha < sim.alphaMin) {
        setMetrics(currentMetrics);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [graphData, mode, selectedCampaignId, hoveredNode, showHulls]);

  // Handle canvas mouse move for interactive node hovering
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !simRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    let nearest: SimNode | null = null;
    let minDist = 22; // Hover detection radius

    for (const node of simRef.current.nodes) {
      const dist = Math.sqrt((node.x - mouseX) ** 2 + (node.y - mouseY) ** 2);
      if (dist < minDist) {
        minDist = dist;
        nearest = node;
      }
    }
    setHoveredNode(nearest);
  }, []);

  // Handle canvas click for node inspection
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !simRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    let clicked: SimNode | null = null;
    let minDist = 25;

    for (const node of simRef.current.nodes) {
      const dist = Math.sqrt((node.x - mouseX) ** 2 + (node.y - mouseY) ** 2);
      if (dist < minDist) {
        minDist = dist;
        clicked = node;
      }
    }
    setSelectedNode(clicked);
  }, []);

  const totalRawNodes = graphData?.nodes?.length || 0;
  const totalDbEntities = graphData?.total_entities_in_db ?? totalRawNodes;
  const availableCampaigns = graphData?.available_campaigns || [];

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header & Mode Controls */}
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
            Deterministic force-directed layout with collision avoidance, centroid attraction, and cluster convex hulls
          </p>
        </div>

        {/* Mode Switcher & Campaign Selector */}
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

          {/* Campaign Selector */}
          {mode === "cluster" && availableCampaigns.length > 0 && (
            <select
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              className="bg-[#121215] text-zinc-200 text-xs rounded-lg px-2.5 py-1.5 border border-[#27272A] focus:outline-none focus:border-rose-500 font-mono"
            >
              {availableCampaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.name.substring(0, 28)}... ({c.email_count} emails)
                </option>
              ))}
            </select>
          )}

          {/* Convex Hull Toggle */}
          <button
            onClick={() => setShowHulls(!showHulls)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono transition-colors ${
              showHulls
                ? "bg-zinc-800 text-zinc-200 border-zinc-700"
                : "bg-zinc-900 text-zinc-500 border-zinc-800"
            }`}
            title="Toggle Campaign Convex Hulls"
          >
            Hulls: {showHulls ? "ON" : "OFF"}
          </button>
        </div>
      </div>

      {/* Physics & Legibility Status Bar */}
      {metrics && (
        <div className="flex flex-wrap items-center justify-between p-2 rounded-lg bg-[#121215] border border-[#27272A] text-[11px] font-mono text-zinc-400 gap-2">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1 text-emerald-400">
              <Activity className="w-3.5 h-3.5" />
              <span>Simulation Settled (0-Collision)</span>
            </span>
            <span>Min Dist: <strong className="text-zinc-200">{metrics.min_pairwise_distance}px</strong></span>
            <span>Avg Dist: <strong className="text-zinc-200">{metrics.avg_pairwise_distance}px</strong></span>
            <span>Hull Ratio: <strong className="text-zinc-200">{metrics.hull_separation_ratio}</strong></span>
          </div>
          <div className="text-zinc-500">
            Deterministic Seed: <strong className="text-zinc-300">#42</strong> | Label Overlaps: <strong className="text-emerald-400">{metrics.label_collisions}</strong>
          </div>
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
        <div className="relative w-full h-[460px] bg-[#0E0E11] rounded-xl border border-[#27272A] flex items-center justify-center overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 bg-[#0E0E11]/70 backdrop-blur-xs flex items-center justify-center text-xs text-zinc-400 z-10">
              Running deterministic force layout simulation...
            </div>
          )}
          <canvas
            ref={canvasRef}
            width={900}
            height={500}
            onMouseMove={handleMouseMove}
            onClick={handleCanvasClick}
            className="w-full h-full cursor-crosshair"
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
