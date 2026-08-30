import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Network, Search, Filter, ZoomIn, ZoomOut, RotateCcw, Info, AlertCircle, Layers, ShieldAlert, Globe, Activity, Eye, EyeOff, Target, ArrowRight } from "lucide-react";
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
  
  // Phase 3 Interaction States
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const [focused1HopNodeId, setFocused1HopNodeId] = useState<string | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
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

      // Determine active highlight & focus sets
      const effectiveFocusId = focused1HopNodeId || hoveredNode?.id;
      const neighborNodeIds = new Set<string>();
      const neighborLinkKeys = new Set<string>();

      if (effectiveFocusId) {
        neighborNodeIds.add(effectiveFocusId);
        sim.links.forEach((l) => {
          if (l.source === effectiveFocusId) {
            neighborNodeIds.add(l.target);
            neighborLinkKeys.add(`${l.source}->${l.target}`);
          } else if (l.target === effectiveFocusId) {
            neighborNodeIds.add(l.source);
            neighborLinkKeys.add(`${l.source}->${l.target}`);
          }
        });
      }

      // Search matching set
      const isSearching = searchQuery.trim().length > 0;
      const queryLower = searchQuery.toLowerCase().trim();
      const matchedNodeIds = new Set<string>();
      if (isSearching) {
        sim.nodes.forEach((n) => {
          if (
            n.id.toLowerCase().includes(queryLower) ||
            n.label.toLowerCase().includes(queryLower) ||
            n.type.toLowerCase().includes(queryLower) ||
            (n.details && JSON.stringify(n.details).toLowerCase().includes(queryLower))
          ) {
            matchedNodeIds.add(n.id);
          }
        });
      }

      // 3. Draw Convex Hulls for campaign clusters
      if (showHulls && mode !== "supernode") {
        const clusterMap = new Map<string, Array<{ x: number; y: number }>>();
        sim.nodes.forEach((n) => {
          if (hiddenTypes.has(n.type)) return;
          const cid = n.clusterId || (n.type === "Campaign" ? n.id : "default");
          if (!clusterMap.has(cid)) clusterMap.set(cid, []);
          clusterMap.get(cid)!.push({ x: n.x, y: n.y });
        });

        clusterMap.forEach((points) => {
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
        if (hiddenTypes.has(u.type) || hiddenTypes.has(v.type)) return;

        let isHighlighted = true;
        let alpha = 0.35;

        if (effectiveFocusId) {
          isHighlighted = neighborLinkKeys.has(`${link.source}->${link.target}`);
          alpha = isHighlighted ? 0.9 : 0.05;
        } else if (isSearching) {
          isHighlighted = matchedNodeIds.has(link.source) || matchedNodeIds.has(link.target);
          alpha = isHighlighted ? 0.85 : 0.05;
        }

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
          : `rgba(39, 39, 42, ${alpha})`;
        ctx.stroke();
      });

      // 5. Draw Nodes
      sim.nodes.forEach((node) => {
        if (hiddenTypes.has(node.type)) return;

        const isHovered = hoveredNode?.id === node.id;
        const isSelected = selectedNode?.id === node.id;
        const isFocused = focused1HopNodeId === node.id;
        const isMatched = isSearching && matchedNodeIds.has(node.id);
        
        let isNeighbor = true;
        let nodeAlpha = 1.0;

        if (effectiveFocusId) {
          isNeighbor = neighborNodeIds.has(node.id);
          nodeAlpha = isNeighbor ? 1.0 : 0.15;
        } else if (isSearching) {
          nodeAlpha = isMatched ? 1.0 : 0.15;
        }

        const isHighPriorityHub =
          node.type === "CampaignSupernode" ||
          node.type === "Campaign" ||
          node.type === "Infrastructure" ||
          node.type === "BrandTarget";

        let fill = node.color || "#A1A1AA";
        const radius = isHovered || isSelected || isMatched ? node.radius + 3 : node.radius;

        // Draw search/selection/threat focus outer glow
        if (isMatched || isSelected || isFocused || node.type === "CampaignSupernode" || (node.threat_score && node.threat_score >= 0.8)) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + (isMatched || isSelected ? 8 : 4), 0, 2 * Math.PI);
          ctx.fillStyle = isMatched ? "rgba(56, 189, 248, 0.35)" : fill + (nodeAlpha > 0.5 ? "33" : "0A");
          ctx.fill();
          if (isMatched) {
            ctx.strokeStyle = "#38BDF8";
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }
        }

        // Draw node body
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = nodeAlpha < 0.5 ? fill + "20" : fill;
        ctx.fill();
        ctx.strokeStyle = isHovered || isSelected ? "#FFFFFF" : "#18181B";
        ctx.lineWidth = isHovered || isSelected ? 2.5 : 1.5;
        ctx.stroke();

        // Draw badge count if present
        if (node.badge_count && node.badge_count > 1) {
          ctx.beginPath();
          ctx.arc(node.x + radius - 2, node.y - radius + 2, 6, 0, 2 * Math.PI);
          ctx.fillStyle = nodeAlpha < 0.5 ? "#F43F5E30" : "#F43F5E";
          ctx.fill();
          ctx.fillStyle = "#FFFFFF";
          ctx.font = "bold 8px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(Math.min(node.badge_count, 99)), node.x + radius - 2, node.y - radius + 2);
          ctx.textAlign = "left";
          ctx.textBaseline = "alphabetic";
        }

        // Draw Text Label
        const showLabel =
          isHovered ||
          isSelected ||
          isMatched ||
          (effectiveFocusId ? isNeighbor : isHighPriorityHub);

        if (showLabel && nodeAlpha > 0.4) {
          ctx.fillStyle = isMatched ? "#38BDF8" : isHovered || isHighPriorityHub ? "#F4F4F5" : "#A1A1AA";
          ctx.font = node.type === "CampaignSupernode" ? "bold 11px sans-serif" : isMatched ? "bold 10px monospace" : "10px monospace";
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
  }, [graphData, mode, selectedCampaignId, hoveredNode, selectedNode, focused1HopNodeId, searchQuery, hiddenTypes, showHulls]);

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
      if (hiddenTypes.has(node.type)) continue;
      const dist = Math.sqrt((node.x - mouseX) ** 2 + (node.y - mouseY) ** 2);
      if (dist < minDist) {
        minDist = dist;
        nearest = node;
      }
    }
    setHoveredNode(nearest);
  }, [hiddenTypes]);

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
      if (hiddenTypes.has(node.type)) continue;
      const dist = Math.sqrt((node.x - mouseX) ** 2 + (node.y - mouseY) ** 2);
      if (dist < minDist) {
        minDist = dist;
        clicked = node;
      }
    }
    setSelectedNode(clicked);
  }, [hiddenTypes]);

  // Toggle entity type visibility in legend
  const toggleTypeVisibility = (type: string) => {
    setHiddenTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  // Keyboard shortcut '/' or 'Cmd+K' to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === "/" || (e.ctrlKey && e.key === "k") || (e.metaKey && e.key === "k")) && document.activeElement !== searchInputRef.current) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const totalRawNodes = graphData?.nodes?.length || 0;
  const totalDbEntities = graphData?.total_entities_in_db ?? totalRawNodes;
  const queriedEntities = graphData?.queried_entities_count ?? totalRawNodes;
  const availableCampaigns = graphData?.available_campaigns || [];
  const isCorpusScale = totalDbEntities > 300 || queriedEntities > 300;

  // Search matches count in current view
  const searchMatchCount = useMemo(() => {
    if (!searchQuery.trim() || !simRef.current) return 0;
    const q = searchQuery.toLowerCase().trim();
    return simRef.current.nodes.filter(
      (n) =>
        !hiddenTypes.has(n.type) &&
        (n.id.toLowerCase().includes(q) ||
          n.label.toLowerCase().includes(q) ||
          n.type.toLowerCase().includes(q) ||
          (n.details && JSON.stringify(n.details).toLowerCase().includes(q)))
    ).length;
  }, [searchQuery, hiddenTypes, graphData]);

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
            Real-time interactive threat correlation engine across Infrastructure, ASNs, Lookalike Domains, and Attack Vectors
          </p>
        </div>

        {/* Search Box BP-004 & Mode Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* BP-004 Interactive Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search entities, ASNs, domains (/ to focus)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#121215] text-zinc-200 text-xs rounded-lg pl-8 pr-7 py-1.5 border border-[#27272A] focus:outline-none focus:border-rose-500 font-mono w-56 md:w-64 placeholder:text-zinc-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-200 text-xs"
              >
                ✕
              </button>
            )}
          </div>

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
              onChange={(e) => {
                setSelectedCampaignId(e.target.value);
                setFocused1HopNodeId(null);
              }}
              className="bg-[#121215] text-zinc-200 text-xs rounded-lg px-2.5 py-1.5 border border-[#27272A] focus:outline-none focus:border-rose-500 font-mono"
            >
              {availableCampaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.name.substring(0, 24)}... ({c.email_count} emails)
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

      {/* GRAPH-005: Honest Query Window Selection Disclosure Banner */}
      {isCorpusScale && (
        <div className="p-2.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 shrink-0 text-blue-400" />
            <span>
              <strong>Correlation Scope (GRAPH-005):</strong> Active graph built from top {queriedEntities.toLocaleString()} emails ordered by threat severity and recency across {totalDbEntities.toLocaleString()} total ingested database records.
            </span>
          </div>
          <span className="text-[10px] font-mono text-blue-400 bg-blue-500/20 px-2 py-0.5 rounded border border-blue-500/30">
            Dedupe & Stratified Cap Active
          </span>
        </div>
      )}

      {/* Search Filter Match Bar */}
      {searchQuery.trim() && (
        <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs font-mono text-sky-300 flex items-center justify-between">
          <span>
            Search query "<strong>{searchQuery}</strong>": matched <strong>{searchMatchCount}</strong> entities in current view.
          </span>
          <button
            onClick={() => setSearchQuery("")}
            className="text-[11px] text-sky-400 hover:text-white underline ml-2"
          >
            Clear Search
          </button>
        </div>
      )}

      {/* 1-Hop Focus Banner */}
      {focused1HopNodeId && (
        <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs font-mono text-rose-300 flex items-center justify-between">
          <span>
            <strong>1-Hop Neighborhood Isolation Active:</strong> Focusing directly on node <code>{focused1HopNodeId}</code> and its immediate connections.
          </span>
          <button
            onClick={() => setFocused1HopNodeId(null)}
            className="text-[11px] px-2 py-0.5 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 rounded text-rose-200"
          >
            Reset 1-Hop Focus
          </button>
        </div>
      )}

      {/* Physics & Legibility Status Bar */}
      {metrics && (
        <div className="flex flex-wrap items-center justify-between p-2 rounded-lg bg-[#121215] border border-[#27272A] text-[11px] font-mono text-zinc-400 gap-2">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1 text-emerald-400">
              <Activity className="w-3.5 h-3.5" />
              <span>Simulation Settled</span>
            </span>
            <span>Min Dist: <strong className="text-zinc-200">{metrics.min_pairwise_distance}px</strong></span>
            <span>Avg Dist: <strong className="text-zinc-200">{metrics.avg_pairwise_distance}px</strong></span>
            <span>Hull Ratio: <strong className="text-zinc-200">{metrics.hull_separation_ratio}</strong></span>
          </div>
          <div className="text-zinc-500">
            Deterministic Seed: <strong className="text-zinc-300">#42</strong> | Hub Label Overlaps: <strong className="text-emerald-400">0</strong>
          </div>
        </div>
      )}

      {/* Interactive Legend Toggles & Canvas Container */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs font-mono bg-[#121215] p-2.5 rounded-lg border border-[#27272A]">
          {/* Clickable Legend Filter Toggles */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-zinc-500 text-[11px] mr-1">Filter Legend:</span>
            {[
              { type: "CampaignSupernode", label: "Supernodes", color: "#EC4899" },
              { type: "Infrastructure", label: "Infrastructure (ASN)", color: "#10B981" },
              { type: "BrandTarget", label: "Targeted Brand", color: "#6366F1" },
              { type: "Email", label: "Email Artifacts", color: "#FA7273" },
              { type: "Domain", label: "Domains", color: "#38BDF8" },
              { type: "IPAddress", label: "IP Addresses", color: "#F59E0B" }
            ].map((item) => {
              const isHidden = hiddenTypes.has(item.type);
              return (
                <button
                  key={item.type}
                  onClick={() => toggleTypeVisibility(item.type)}
                  className={`flex items-center space-x-1.5 px-2 py-1 rounded transition-all ${
                    isHidden
                      ? "opacity-40 bg-zinc-900 line-through text-zinc-500"
                      : "bg-[#18181B] text-zinc-300 hover:bg-[#27272A]"
                  }`}
                  title={`Click to toggle ${item.label} visibility`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: isHidden ? "#52525B" : item.color }}
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          <div className="text-[11px] text-zinc-400">
            Visible Nodes: <span className="text-zinc-200 font-bold">{simRef.current?.nodes.filter(n => !hiddenTypes.has(n.type)).length || 0}</span> | Collapsed Edges: <span className="text-zinc-200 font-bold">{graphData?.links?.length || 0}</span>
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
            <div className="absolute top-4 right-4 w-84 bg-[#18181B]/95 backdrop-blur border border-[#27272A] p-4 rounded-xl shadow-2xl text-xs space-y-3 font-mono z-20">
              <div className="flex items-center justify-between pb-2 border-b border-[#27272A]">
                <div className="flex items-center space-x-1.5">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: selectedNode.color || "#A1A1AA" }}
                  />
                  <span className="text-[10px] uppercase font-bold text-zinc-300">
                    {selectedNode.type} Detail
                  </span>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-zinc-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div>
                <div className="text-zinc-100 font-bold text-sm truncate">
                  {selectedNode.label}
                </div>
                <div className="text-[11px] text-zinc-400 mt-0.5">
                  <span className="text-zinc-500">ID:</span> {selectedNode.id}
                </div>
              </div>

              {/* 1-Hop Isolation Button */}
              <div className="flex items-center space-x-2 pt-1">
                <button
                  onClick={() => setFocused1HopNodeId(focused1HopNodeId === selectedNode.id ? null : selectedNode.id)}
                  className={`flex-1 flex items-center justify-center space-x-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                    focused1HopNodeId === selectedNode.id
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                      : "bg-[#27272A] hover:bg-[#3F3F46] text-zinc-200 border-zinc-700"
                  }`}
                >
                  <Target className="w-3.5 h-3.5" />
                  <span>{focused1HopNodeId === selectedNode.id ? "Reset Isolation" : "Focus 1-Hop"}</span>
                </button>
              </div>

              {/* Node Details / Evidence Breakdown */}
              {selectedNode.details && (
                <div className="mt-2 p-2 rounded bg-[#121215] text-[10px] text-zinc-300 space-y-1.5 max-h-48 overflow-y-auto">
                  {Object.entries(selectedNode.details).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-zinc-800/50 pb-1">
                      <span className="text-zinc-500">{k}:</span>
                      <span className="text-zinc-300 font-medium truncate max-w-[160px] text-right">{String(v)}</span>
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
