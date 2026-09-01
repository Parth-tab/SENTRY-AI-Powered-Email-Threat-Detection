import { GraphNode, GraphLink } from "../../types";

export interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  clusterId?: string;
  isSupernode?: boolean;
}

export interface SimLink {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  sourceNode: SimNode;
  targetNode: SimNode;
}

export interface GraphMetrics {
  rendered_nodes: number;
  rendered_links: number;
  min_pairwise_distance: number;
  avg_pairwise_distance: number;
  hull_separation_ratio: number;
  edge_node_ratio: number;
  label_collisions: number;
  hub_label_collisions: number;
  is_simulation_settled: boolean;
  active_mode: string;
  active_campaign_id: string | null;
  seed: number;
}

// 1. Seeded PRNG (Mulberry32) for 100% deterministic simulation
export function createRNG(seed: number = 42) {
  let s = seed >>> 0;
  return function () {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 2. Monotone Chain 2D Convex Hull Algorithm
export function computeConvexHull(points: Array<{ x: number; y: number }>): Array<{ x: number; y: number }> {
  if (points.length <= 2) return points;

  const sorted = points.slice().sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x));

  const crossProduct = (o: { x: number; y: number }, a: { x: number; y: number }, b: { x: number; y: number }) =>
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

  const lower: Array<{ x: number; y: number }> = [];
  for (const p of sorted) {
    while (lower.length >= 2 && crossProduct(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  const upper: Array<{ x: number; y: number }> = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && crossProduct(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  upper.pop();
  lower.pop();
  return lower.concat(upper);
}

// 3. Complete Physics Force Simulation Engine
export class GraphSimulation {
  public nodes: SimNode[] = [];
  public links: SimLink[] = [];
  public alpha: number = 1.0;
  public alphaMin: number = 0.003;
  public alphaDecay: number = 0.02;
  public width: number;
  public height: number;
  public mode: "cluster" | "supernode" | "detailed";
  private rng: () => number;

  constructor(width: number, height: number, mode: "cluster" | "supernode" | "detailed" = "cluster", seed: number = 42) {
    this.width = width;
    this.height = height;
    this.mode = mode;
    this.rng = createRNG(seed);
  }

  public initData(rawNodes: GraphNode[], rawLinks: GraphLink[], maxNodes: number = 300) {
    const cappedNodes = rawNodes.slice(0, maxNodes);
    const cappedNodeIds = new Set(cappedNodes.map((n) => n.id));
    const cx = this.width / 2;
    const cy = this.height / 2;

    // Per-mode initial positioning
    this.nodes = cappedNodes.map((n, i) => {
      let radius = 8;
      const isSuper = n.type === "CampaignSupernode";
      if (isSuper) radius = 15;
      else if (n.type === "Campaign") radius = 13;
      else if (n.type === "Infrastructure") radius = 10;
      else if (n.type === "BrandTarget") radius = 10;
      else if (n.type === "Domain") radius = 8;
      else if (n.type === "IPAddress") radius = 8;
      else if (n.type === "Email") radius = 6;

      // Deterministic initial placement
      let initX = cx;
      let initY = cy;

      if (this.mode === "supernode") {
        const angle = (i / Math.max(cappedNodes.length, 1)) * 2 * Math.PI;
        const dist = isSuper ? 80 : 170 + (i % 2) * 50;
        initX = cx + Math.cos(angle) * dist;
        initY = cy + Math.sin(angle) * dist;
      } else if (this.mode === "cluster") {
        const isCamp = n.type === "Campaign" || n.type === "CampaignSupernode";
        if (isCamp) {
          initX = cx;
          initY = cy;
        } else {
          const angle = (i / Math.max(cappedNodes.length, 1)) * 2 * Math.PI;
          const dist = 110 + this.rng() * 130;
          initX = cx + Math.cos(angle) * dist;
          initY = cy + Math.sin(angle) * dist;
        }
      } else {
        // Detailed multi-cluster mode
        const campHash = n.campaign_id ? Math.abs(this.hashCode(n.campaign_id)) % 3 : i % 3;
        const clusterAngle = (campHash / 3) * 2 * Math.PI - Math.PI / 2;
        const clusterCenterX = cx + Math.cos(clusterAngle) * 190;
        const clusterCenterY = cy + Math.sin(clusterAngle) * 140;

        const subAngle = this.rng() * 2 * Math.PI;
        const subDist = this.rng() * 95;
        initX = clusterCenterX + Math.cos(subAngle) * subDist;
        initY = clusterCenterY + Math.sin(subAngle) * subDist;
      }

      return {
        ...n,
        x: initX,
        y: initY,
        vx: (this.rng() - 0.5) * 2,
        vy: (this.rng() - 0.5) * 2,
        radius,
        isSupernode: isSuper,
        clusterId: n.campaign_id || (n.details?.campaign_id ?? undefined)
      };
    });

    const nodeMap = new Map(this.nodes.map((n) => [n.id, n]));

    this.links = rawLinks
      .filter((l) => cappedNodeIds.has(l.source) && cappedNodeIds.has(l.target))
      .map((l) => ({
        source: l.source,
        target: l.target,
        relationship: l.relationship,
        weight: l.weight || 1,
        sourceNode: nodeMap.get(l.source) || this.nodes[0],
        targetNode: nodeMap.get(l.target) || this.nodes[0]
      }))
      .filter((l) => l.sourceNode && l.targetNode);

    this.alpha = 1.0;
  }

  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) - hash + str.charCodeAt(i);
      hash |= 0;
    }
    return hash;
  }

  // Physics Simulation Step
  public tick() {
    if (this.alpha < this.alphaMin) {
      this.alpha = 0;
      return;
    }

    const cx = this.width / 2;
    const cy = this.height / 2;
    const nodes = this.nodes;
    const links = this.links;
    const n = nodes.length;

    // Force Parameters tuned per mode
    let chargeStrength = -420;
    let linkDistance = 110;
    let collidePadding = 30;
    let centerPull = 0.018;

    if (this.mode === "supernode") {
      chargeStrength = -850;
      linkDistance = 175;
      collidePadding = 35;
      centerPull = 0.01;
    } else if (this.mode === "detailed") {
      chargeStrength = -280;
      linkDistance = 80;
      collidePadding = 22;
      centerPull = 0.015;
    }

    // 1. Many-Body Repulsion (Coulomb Repulsion)
    for (let i = 0; i < n; i++) {
      const nodeA = nodes[i];
      const isHubA =
        nodeA.type === "CampaignSupernode" ||
        nodeA.type === "Campaign" ||
        nodeA.type === "Infrastructure" ||
        nodeA.type === "BrandTarget";

      for (let j = i + 1; j < n; j++) {
        const nodeB = nodes[j];
        const isHubB =
          nodeB.type === "CampaignSupernode" ||
          nodeB.type === "Campaign" ||
          nodeB.type === "Infrastructure" ||
          nodeB.type === "BrandTarget";

        let dx = nodeB.x - nodeA.x;
        let dy = nodeB.y - nodeA.y;
        let distSq = dx * dx + dy * dy;
        if (distSq < 1) {
          dx = (this.rng() - 0.5) * 2;
          dy = (this.rng() - 0.5) * 2;
          distSq = dx * dx + dy * dy;
        }

        const dist = Math.sqrt(distSq);
        const hubMultiplier = isHubA && isHubB ? 2.5 : isHubA || isHubB ? 1.5 : 1.0;
        const force = (chargeStrength * hubMultiplier * this.alpha) / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        nodeA.vx += fx;
        nodeA.vy += fy;
        nodeB.vx -= fx;
        nodeB.vy -= fy;
      }
    }

    // 2. Spring Link Attraction (Hooke's Law)
    for (const link of links) {
      const u = link.sourceNode;
      const v = link.targetNode;
      let dx = v.x - u.x;
      let dy = v.y - u.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 1;

      // Adjust link distance by relationship weight
      const targetDist = linkDistance / Math.sqrt(link.weight || 1);
      const delta = (dist - targetDist) / dist;
      const springK = 0.09 * this.alpha;

      const fx = dx * delta * springK;
      const fy = dy * delta * springK;

      u.vx += fx;
      u.vy += fy;
      v.vx -= fx;
      v.vy -= fy;
    }

    // 3. Collision Avoidance (forceCollide)
    for (let i = 0; i < n; i++) {
      const nodeA = nodes[i];
      const isHubA =
        nodeA.type === "CampaignSupernode" ||
        nodeA.type === "Campaign" ||
        nodeA.type === "Infrastructure" ||
        nodeA.type === "BrandTarget";
      for (let j = i + 1; j < n; j++) {
        const nodeB = nodes[j];
        const isHubB =
          nodeB.type === "CampaignSupernode" ||
          nodeB.type === "Campaign" ||
          nodeB.type === "Infrastructure" ||
          nodeB.type === "BrandTarget";
        let dx = nodeB.x - nodeA.x;
        let dy = nodeB.y - nodeA.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const extraHubPadding = isHubA && isHubB ? 20 : 0;
        const minDist = nodeA.radius + nodeB.radius + collidePadding + extraHubPadding;

        if (dist < minDist) {
          const overlap = (minDist - dist) / dist;
          const resolveX = dx * overlap * 0.5;
          const resolveY = dy * overlap * 0.5;

          nodeA.x -= resolveX;
          nodeA.y -= resolveY;
          nodeB.x += resolveX;
          nodeB.y += resolveY;

          nodeA.vx -= resolveX * 0.2;
          nodeA.vy -= resolveY * 0.2;
          nodeB.vx += resolveX * 0.2;
          nodeB.vy += resolveY * 0.2;
        }
      }
    }

    // 4. Center & Bounds Attraction
    for (let i = 0; i < n; i++) {
      const node = nodes[i];
      node.vx += (cx - node.x) * centerPull * this.alpha;
      node.vy += (cy - node.y) * centerPull * this.alpha;

      // Velocity integration and damping
      node.x += node.vx;
      node.y += node.vy;
      node.vx *= 0.88;
      node.vy *= 0.88;

      // Canvas boundary safety
      const pad = node.radius + 20;
      node.x = Math.max(pad, Math.min(this.width - pad, node.x));
      node.y = Math.max(pad, Math.min(this.height - pad, node.y));
    }

    // Decay alpha
    this.alpha += (0 - this.alpha) * this.alphaDecay;
  }

  // 4. Calculate Legibility & Geometric Metrics (window.__graphMetrics) - Filter-Aware (P3-B)
  public getMetrics(
    activeCampaignId: string | null = null,
    seed: number = 42,
    hiddenTypes: Set<string> = new Set()
  ): GraphMetrics {
    const nodes = this.nodes.filter((n) => !hiddenTypes.has(n.type));
    const nodeIds = new Set(nodes.map((n) => n.id));
    const links = this.links.filter((l) => nodeIds.has(l.source) && nodeIds.has(l.target));
    const n = nodes.length;

    let minPairwise = Infinity;
    let totalDist = 0;
    let pairCount = 0;

    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minPairwise) minPairwise = dist;
        totalDist += dist;
        pairCount++;
      }
    }

    const avgPairwise = pairCount > 0 ? totalDist / pairCount : 0;
    const safeMinPairwise = minPairwise === Infinity ? 0 : minPairwise;

    // Label collision calculation based on prominent label policy on visible nodes
    let labelCollisions = 0;
    const labeledNodes = nodes; // MUTATION 2: Force all nodes to label unconditionally

    const m = labeledNodes.length;
    for (let i = 0; i < m; i++) {
      const a = labeledNodes[i];
      const aBox = { x1: a.x + a.radius + 4, x2: a.x + a.radius + 70, y1: a.y - 6, y2: a.y + 6 };
      for (let j = i + 1; j < m; j++) {
        const b = labeledNodes[j];
        const bBox = { x1: b.x + b.radius + 4, x2: b.x + b.radius + 70, y1: b.y - 6, y2: b.y + 6 };
        if (aBox.x1 < bBox.x2 && aBox.x2 > bBox.x1 && aBox.y1 < bBox.y2 && aBox.y2 > bBox.y1) {
          labelCollisions++;
        }
      }
    }

    // Hull separation ratio across clusters
    const clusters = new Map<string, SimNode[]>();
    for (const node of nodes) {
      const cid = node.clusterId || "default";
      if (!clusters.has(cid)) clusters.set(cid, []);
      clusters.get(cid)!.push(node);
    }

    let hullSepRatio = 1.0;
    if (clusters.size >= 2) {
      const clusterCenters: Array<{ x: number; y: number; radius: number }> = [];
      for (const [cid, cNodes] of clusters.entries()) {
        const avgX = cNodes.reduce((acc, cur) => acc + cur.x, 0) / cNodes.length;
        const avgY = cNodes.reduce((acc, cur) => acc + cur.y, 0) / cNodes.length;
        const maxR = Math.max(...cNodes.map((cn) => Math.sqrt((cn.x - avgX) ** 2 + (cn.y - avgY) ** 2)), 30);
        clusterCenters.push({ x: avgX, y: avgY, radius: maxR });
      }

      let minCentroidDist = Infinity;
      let sumRadii = 1;
      for (let i = 0; i < clusterCenters.length; i++) {
        for (let j = i + 1; j < clusterCenters.length; j++) {
          const cA = clusterCenters[i];
          const cB = clusterCenters[j];
          const dist = Math.sqrt((cB.x - cA.x) ** 2 + (cB.y - cA.y) ** 2);
          if (dist < minCentroidDist) {
            minCentroidDist = dist;
            sumRadii = cA.radius + cB.radius;
          }
        }
      }
      hullSepRatio = sumRadii > 0 && minCentroidDist !== Infinity ? minCentroidDist / sumRadii : 1.2;
    }

    // Hub Label collision count (Radial Box Check)
    let hubCollisions = 0;
    const cx = this.width / 2;
    const hubNodes = nodes.filter(
      (node) =>
        node.type === "CampaignSupernode" ||
        node.type === "Campaign" ||
        node.type === "Infrastructure" ||
        node.type === "BrandTarget"
    );
    for (let i = 0; i < hubNodes.length; i++) {
      const a = hubNodes[i];
      const isLeftA = a.x < cx;
      const aBox = isLeftA
        ? { x1: a.x - a.radius - 60, x2: a.x - a.radius - 2, y1: a.y - 6, y2: a.y + 6 }
        : { x1: a.x + a.radius + 2, x2: a.x + a.radius + 60, y1: a.y - 6, y2: a.y + 6 };
      for (let j = i + 1; j < hubNodes.length; j++) {
        const b = hubNodes[j];
        const isLeftB = b.x < cx;
        const bBox = isLeftB
          ? { x1: b.x - b.radius - 60, x2: b.x - b.radius - 2, y1: b.y - 6, y2: b.y + 6 }
          : { x1: b.x + b.radius + 2, x2: b.x + b.radius + 60, y1: b.y - 6, y2: b.y + 6 };
        if (aBox.x1 < bBox.x2 && aBox.x2 > bBox.x1 && aBox.y1 < bBox.y2 && aBox.y2 > bBox.y1) {
          hubCollisions++;
        }
      }
    }

    return {
      rendered_nodes: n,
      rendered_links: links.length,
      min_pairwise_distance: Math.round(safeMinPairwise * 10) / 10,
      avg_pairwise_distance: Math.round(avgPairwise * 10) / 10,
      hull_separation_ratio: Math.round(hullSepRatio * 100) / 100,
      edge_node_ratio: n > 0 ? Math.round((links.length / n) * 100) / 100 : 0,
      label_collisions: labelCollisions,
      hub_label_collisions: hubCollisions,
      is_simulation_settled: this.alpha < this.alphaMin,
      active_mode: this.mode,
      active_campaign_id: activeCampaignId,
      seed
    };
  }
}

