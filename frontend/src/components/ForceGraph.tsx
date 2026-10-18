"use client";

import React, { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Subgraph, SubgraphNode } from "../lib/types";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

// Dynamic import with ssr: false as required by DEV_B_SPEC_v2.md
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface Props {
  subgraph: Subgraph;
  activeTab?: string;
}

// Color tokens for node types tuned for elegant luminous light theme
const TYPE_COLORS: Record<string, string> = {
  System: "#0284c7", // Sky 600
  Person: "#7c3aed", // Purple 600
  Team: "#db2777", // Pink 600
  Ticket: "#ea580c", // Orange 600
  PullRequest: "#4f46e5", // Indigo 600
  SlackThread: "#d97706", // Amber 600
  Document: "#0891b2", // Cyan 600
  Decision: "#059669", // Emerald 600
  Playbook: "#0d9488", // Teal 600
  TenantGraph: "#6366f1",
};

/**
 * Computes deterministic level-based layout coordinates.
 * Eliminates spring bouncing, elastic rubber stretching, and node overlapping.
 */
function computeCleanLayout(nodes: any[], edges: any[]) {
  const inDegree = new Map<string, number>();
  const outEdges = new Map<string, string[]>();

  nodes.forEach((n) => {
    inDegree.set(n.id, 0);
    outEdges.set(n.id, []);
  });

  edges.forEach((e) => {
    const sId = typeof e.source === "object" ? e.source.id : e.source;
    const tId = typeof e.target === "object" ? e.target.id : e.target;
    if (inDegree.has(tId)) {
      inDegree.set(tId, (inDegree.get(tId) || 0) + 1);
    }
    if (outEdges.has(sId)) {
      outEdges.get(sId)!.push(tId);
    }
  });

  // Calculate hierarchical levels via BFS from root nodes
  const levels = new Map<string, number>();
  const queue: string[] = [];

  nodes.forEach((n) => {
    if ((inDegree.get(n.id) || 0) === 0) {
      levels.set(n.id, 0);
      queue.push(n.id);
    }
  });

  // Fallback if graph has a cycle or no root
  if (queue.length === 0 && nodes.length > 0) {
    levels.set(nodes[0].id, 0);
    queue.push(nodes[0].id);
  }

  while (queue.length > 0) {
    const curr = queue.shift()!;
    const currLevel = levels.get(curr) || 0;
    const neighbors = outEdges.get(curr) || [];
    for (const next of neighbors) {
      if (!levels.has(next) || levels.get(next)! < currLevel + 1) {
        levels.set(next, currLevel + 1);
        queue.push(next);
      }
    }
  }

  // Assign level 0 to any unreached nodes
  nodes.forEach((n) => {
    if (!levels.has(n.id)) {
      levels.set(n.id, 0);
    }
  });

  // Group nodes by level
  const byLevel = new Map<number, any[]>();
  nodes.forEach((n) => {
    const lvl = levels.get(n.id) || 0;
    if (!byLevel.has(lvl)) byLevel.set(lvl, []);
    byLevel.get(lvl)!.push(n);
  });

  const maxLvl = Math.max(...Array.from(byLevel.keys()), 0);

  // Assign fixed coordinates with generous clearance
  byLevel.forEach((levelNodes, lvl) => {
    const count = levelNodes.length;
    levelNodes.forEach((node, idx) => {
      // 240px horizontal spacing ensures full names never collide
      const x = (idx - (count - 1) / 2) * 240;
      // 115px vertical spacing gives generous clearance between levels
      const y = (lvl - maxLvl / 2) * 115;
      node.fx = x;
      node.fy = y;
      node.x = x;
      node.y = y;
    });
  });

  return nodes;
}

export const ForceGraph: React.FC<Props> = ({ subgraph, activeTab }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 420 });

  // Dynamically update dimensions matching parent container's bounding client dimensions
  useEffect(() => {
    if (!containerRef.current) return;
    const updateSize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        if (clientWidth > 50 && clientHeight > 50) {
          setDimensions({
            width: clientWidth,
            height: clientHeight,
          });
        }
      }
    };

    updateSize();

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 50 && height > 50) {
          setDimensions({
            width: Math.floor(width),
            height: Math.floor(height),
          });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Auto-center & zoom-to-fit triggered when active subgraph or active tab changes
  useEffect(() => {
    if (!subgraph?.nodes || subgraph.nodes.length === 0) return;
    const timer = setTimeout(() => {
      fgRef.current?.zoomToFit(350, 65);
    }, 150);
    return () => clearTimeout(timer);
  }, [subgraph, activeTab]);

  const handleRecenter = () => {
    fgRef.current?.zoomToFit(400, 65);
  };

  const handleZoomIn = () => {
    if (fgRef.current) {
      const curr = fgRef.current.zoom();
      fgRef.current.zoom(Math.min(curr * 1.3, 1.4), 200);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      const curr = fgRef.current.zoom();
      fgRef.current.zoom(Math.max(curr / 1.3, 0.4), 200);
    }
  };

  if (!subgraph?.nodes || subgraph.nodes.length === 0) {
    return (
      <div
        ref={containerRef}
        className="flex h-full min-h-[380px] w-full flex-col items-center justify-center rounded-xl border border-slate-200 bg-white/70 p-6 text-center shadow-sm"
      >
        <div className="text-3xl mb-2 opacity-80">🌐</div>
        <p className="text-sm font-semibold text-slate-800">
          No active traversal subgraph
        </p>
        <p className="mt-1 text-xs text-slate-500 max-w-xs leading-relaxed">
          Click any Golden Demo Scenario or ask a question to visualize
          traversed nodes and multi-hop provenance edges.
        </p>
      </div>
    );
  }

  // Pre-process nodes & edges with deterministic coordinates
  const rawNodes = subgraph.nodes.map((n) => {
    const rawLabel = String(n.label || n.id || "").trim();
    // Allow up to 28 characters so standard names and titles show completely without truncation
    const displayLabel = rawLabel.length > 28 ? rawLabel.slice(0, 26) + "…" : rawLabel;
    const estimatedWidth = Math.max(displayLabel.length * 6.8 + 36, 92);

    return {
      ...n,
      __displayLabel: displayLabel,
      __width: estimatedWidth,
      __height: 26,
    };
  });

  const edges = subgraph.edges.map((e) => ({
    source: typeof e.source === "object" ? (e.source as SubgraphNode).id : e.source,
    target: typeof e.target === "object" ? (e.target as SubgraphNode).id : e.target,
    relationship: e.relationship,
  }));

  // Apply clean deterministic coordinates to eliminate all overlap and rubber-band motion
  const nodes = computeCleanLayout(rawNodes, edges);
  const graphData = { nodes, links: edges };

  return (
    <div
      ref={containerRef}
      className="relative h-full min-h-[380px] w-full overflow-hidden rounded-xl border border-slate-200 bg-[#f8fafc]"
    >
      {/* Floating HUD Controls (Top-Right) */}
      <div className="absolute top-2.5 right-2.5 z-20 flex items-center gap-1.5 rounded-lg border border-slate-200/90 bg-white/95 p-1 backdrop-blur-md shadow-sm">
        <span className="px-2 font-mono text-[10px] text-slate-600 border-r border-slate-200 select-none">
          {nodes.length} nodes · {edges.length} edges
        </span>
        <button
          type="button"
          onClick={handleZoomIn}
          title="Zoom In"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          title="Zoom Out"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={handleRecenter}
          title="Fit & Recenter Graph"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition"
        >
          <Maximize2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Visual Canvas */}
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        minZoom={0.4}
        maxZoom={1.25}
        cooldownTicks={80}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 65)}
        d3VelocityDecay={0.88}
        d3AlphaDecay={0.08}
        enableNodeDrag={true}
        onNodeDrag={(node: any) => {
          node.fx = node.x;
          node.fy = node.y;
        }}
        onNodeDragEnd={(node: any) => {
          node.fx = node.x;
          node.fy = node.y;
        }}
        nodeLabel={(node: any) =>
          `${node.type}: ${node.label || node.id} (${node.status || "active"})`
        }
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const w = node.__width || 100;
          const h = node.__height || 26;
          ctx.fillStyle = color;
          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(node.x - w / 2, node.y - h / 2, w, h, 13);
          } else {
            ctx.rect(node.x - w / 2, node.y - h / 2, w, h);
          }
          ctx.fill();
        }}
        nodeCanvasObjectMode={() => "replace"}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, _globalScale: number) => {
          const w = node.__width || 100;
          const h = node.__height || 26;
          const x = node.x - w / 2;
          const y = node.y - h / 2;
          const status = (node.status || "active").toLowerCase();
          const nodeColor =
            status === "superseded"
              ? "#dc2626"
              : status === "outdated"
              ? "#d97706"
              : TYPE_COLORS[node.type] || "#64748b";

          // 1. Unified Capsule Card Body (Both status dot and text inside one card)
          ctx.save();
          ctx.shadowColor = "rgba(15, 23, 42, 0.08)";
          ctx.shadowBlur = 5;
          ctx.shadowOffsetY = 2;

          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(x, y, w, h, 13);
          } else {
            ctx.rect(x, y, w, h);
          }
          ctx.fillStyle = "#ffffff";
          ctx.fill();
          ctx.restore();

          // 2. Card Border
          ctx.save();
          if (status === "active" && node.type === "Decision") {
            ctx.strokeStyle = "#059669";
            ctx.lineWidth = 1.6;
          } else if (status === "superseded") {
            ctx.strokeStyle = "#dc2626";
            ctx.lineWidth = 1.6;
            ctx.setLineDash([3, 2]);
          } else {
            ctx.strokeStyle = "rgba(15, 23, 42, 0.14)";
            ctx.lineWidth = 1.1;
          }

          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(x, y, w, h, 13);
          } else {
            ctx.rect(x, y, w, h);
          }
          ctx.stroke();
          ctx.restore();

          // 3. Status / Type Dot Indicator on the Left
          const dotRadius = 4;
          const dotX = x + 11;
          const dotY = node.y;

          if (status === "active" && node.type === "Decision") {
            ctx.beginPath();
            ctx.arc(dotX, dotY, dotRadius + 2.5, 0, 2 * Math.PI);
            ctx.strokeStyle = "rgba(5, 150, 105, 0.4)";
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }

          ctx.beginPath();
          ctx.arc(dotX, dotY, dotRadius, 0, 2 * Math.PI);
          ctx.fillStyle = nodeColor;
          ctx.fill();

          // 4. Text Label inside the capsule (vertically centered, guaranteed zero overlap)
          const textX = dotX + 7;
          ctx.font = `600 10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
          ctx.fillStyle = status === "superseded" ? "#991b1b" : "#0f172a";
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillText(node.__displayLabel || node.id, textX, node.y);
        }}
        linkColor={(link: any) =>
          link.relationship === "SUPERSEDES" ? "#dc2626" : "#94a3b8"
        }
        linkWidth={(link: any) =>
          link.relationship === "SUPERSEDES" ? 2.0 : 1.2
        }
        linkDirectionalArrowLength={5.5}
        linkDirectionalArrowRelPos={0.86}
        linkCanvasObjectMode={() => "after"}
        linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, _globalScale: number) => {
          if (link.relationship) {
            const start = link.source;
            const end = link.target;
            if (
              typeof start === "object" &&
              typeof end === "object" &&
              start.x != null &&
              end.x != null
            ) {
              const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2,
              };
              const rel = String(link.relationship);
              const fontSize = 8;
              ctx.font = `700 ${fontSize}px "JetBrains Mono", Menlo, monospace`;
              const textWidth = ctx.measureText(rel).width;
              const pillW = textWidth + 8;
              const pillH = fontSize + 6;
              const pillX = textPos.x - pillW / 2;
              const pillY = textPos.y - pillH / 2;

              ctx.fillStyle = "#ffffff";
              ctx.strokeStyle =
                rel === "SUPERSEDES"
                  ? "rgba(220, 38, 38, 0.45)"
                  : "rgba(15, 23, 42, 0.14)";
              ctx.lineWidth = 0.8;

              if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(pillX, pillY, pillW, pillH, 4);
                ctx.fill();
                ctx.stroke();
              } else {
                ctx.fillRect(pillX, pillY, pillW, pillH);
                ctx.strokeRect(pillX, pillY, pillW, pillH);
              }

              ctx.fillStyle =
                rel === "SUPERSEDES" ? "#dc2626" : "#475569";
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillText(rel, textPos.x, textPos.y);
            }
          }
        }}
      />

      {/* Floating Legend (Bottom-Left) */}
      <div className="pointer-events-none absolute bottom-2.5 left-2.5 z-20 flex flex-wrap gap-2.5 rounded-lg border border-slate-200/90 bg-white/95 px-3 py-1.5 backdrop-blur-md text-[10px] text-slate-700 shadow-sm">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-600 ring-2 ring-emerald-500/30" />
          Active ADR
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-rose-600 ring-2 ring-rose-500/30" />
          Superseded
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-sky-600" />
          System
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-purple-600" />
          Person
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-pink-600" />
          Team
        </span>
      </div>
    </div>
  );
};
