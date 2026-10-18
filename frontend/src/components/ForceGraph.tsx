"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { Subgraph, SubgraphNode } from "../lib/types";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

// Dynamic import with ssr: false as required by DEV_B_SPEC_v2.md
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface Props {
  subgraph: Subgraph;
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

export const ForceGraph: React.FC<Props> = ({ subgraph }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 420 });

  // Dynamically update dimensions via ResizeObserver
  useEffect(() => {
    if (!containerRef.current) return;
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

  // Configure physics forces & camera auto-fit on graph data updates
  const autoFitGraph = useCallback(() => {
    if (fgRef.current) {
      // Repulsion force to prevent node clumping
      fgRef.current.d3Force("charge")?.strength(-380);
      // Link distance to ensure clear space for relationship badges
      fgRef.current.d3Force("link")?.distance(105);
      // Auto-fit camera with generous padding
      fgRef.current.zoomToFit(400, 65);
    }
  }, []);

  useEffect(() => {
    if (!subgraph?.nodes || subgraph.nodes.length === 0) return;

    // Trigger auto-fit after simulation starts spreading nodes
    const timer1 = setTimeout(autoFitGraph, 250);
    const timer2 = setTimeout(autoFitGraph, 700);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [subgraph, autoFitGraph]);

  const handleRecenter = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 60);
    }
  };

  const handleZoomIn = () => {
    if (fgRef.current) {
      const curr = fgRef.current.zoom();
      fgRef.current.zoom(Math.min(curr * 1.35, 3.2), 250);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      const curr = fgRef.current.zoom();
      fgRef.current.zoom(Math.max(curr / 1.35, 0.45), 250);
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

  // Pre-process nodes & edges
  const nodes = subgraph.nodes.map((n) => ({ ...n }));
  const edges = subgraph.edges.map((e) => ({
    source: typeof e.source === "object" ? (e.source as SubgraphNode).id : e.source,
    target: typeof e.target === "object" ? (e.target as SubgraphNode).id : e.target,
    relationship: e.relationship,
  }));

  const graphData = { nodes, links: edges };

  return (
    <div
      ref={containerRef}
      className="relative h-full min-h-[380px] w-full overflow-hidden rounded-xl border border-slate-200 bg-[#f8fafc]"
    >
      {/* Floating HUD Controls (Top-Right) */}
      <div className="absolute top-2.5 right-2.5 z-20 flex items-center gap-1.5 rounded-lg border border-slate-200/90 bg-white/90 p-1 backdrop-blur-md shadow-sm">
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
        minZoom={0.45}
        maxZoom={3.2}
        d3VelocityDecay={0.28}
        cooldownTicks={120}
        onEngineStop={autoFitGraph}
        nodeLabel={(node: any) =>
          `${node.type}: ${node.label || node.id} (${node.status || "active"})`
        }
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 11, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        nodeCanvasObjectMode={() => "replace"}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const r = node.type === "Decision" ? 9 : 8;
          const status = (node.status || "active").toLowerCase();
          const nodeColor =
            status === "superseded"
              ? "#dc2626"
              : status === "outdated"
              ? "#d97706"
              : TYPE_COLORS[node.type] || "#64748b";

          // 1. Halo / Glow Ring for Special Statuses
          if (status === "active" && node.type === "Decision") {
            ctx.save();
            ctx.shadowColor = "rgba(5, 150, 105, 0.4)";
            ctx.shadowBlur = 8;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#059669";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
          } else if (status === "superseded") {
            ctx.save();
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 2.5, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#dc2626";
            ctx.lineWidth = 1.6;
            ctx.setLineDash([3, 2]);
            ctx.stroke();
            ctx.restore();
          }

          // 2. Main Node Body
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
          ctx.fillStyle = nodeColor;
          ctx.fill();
          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 1.6;
          ctx.stroke();

          // 3. Node Label Badge (Clean Pill Background to prevent text collisions)
          const rawLabel = String(node.label || node.id || "").trim();
          const displayLabel = rawLabel.length > 22 ? rawLabel.slice(0, 20) + "…" : rawLabel;

          // Keep font size clamped within readable bounds
          const fontSize = Math.min(Math.max(10 / globalScale, 6.5), 11);
          ctx.font = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
          const textWidth = ctx.measureText(displayLabel).width;
          const pillPaddingX = 5;
          const pillPaddingY = 2;
          const pillH = fontSize + pillPaddingY * 2;
          const pillW = textWidth + pillPaddingX * 2;
          const pillX = node.x - pillW / 2;
          const pillY = node.y + r + 3;

          ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
          ctx.strokeStyle = "rgba(15, 23, 42, 0.14)";
          ctx.lineWidth = 0.9;
          if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(pillX, pillY, pillW, pillH, 3.5);
            ctx.fill();
            ctx.stroke();
          } else {
            ctx.fillRect(pillX, pillY, pillW, pillH);
            ctx.strokeRect(pillX, pillY, pillW, pillH);
          }

          ctx.fillStyle = "#0f172a";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(displayLabel, node.x, pillY + pillH / 2);
        }}
        linkColor={(link: any) =>
          link.relationship === "SUPERSEDES" ? "#dc2626" : "#cbd5e1"
        }
        linkWidth={(link: any) =>
          link.relationship === "SUPERSEDES" ? 2.2 : 1.2
        }
        linkDirectionalArrowLength={4.5}
        linkDirectionalArrowRelPos={0.88}
        linkCanvasObjectMode={() => "after"}
        linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
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
              const fontSize = Math.min(Math.max(7.5 / globalScale, 5.5), 8.5);
              ctx.font = `600 ${fontSize}px "JetBrains Mono", Menlo, monospace`;
              const textWidth = ctx.measureText(rel).width;
              const pillW = textWidth + 6;
              const pillH = fontSize + 4;
              const pillX = textPos.x - pillW / 2;
              const pillY = textPos.y - pillH / 2;

              ctx.fillStyle = "rgba(255, 255, 255, 0.96)";
              ctx.strokeStyle =
                rel === "SUPERSEDES"
                  ? "rgba(220, 38, 38, 0.4)"
                  : "rgba(15, 23, 42, 0.12)";
              ctx.lineWidth = 0.8;

              if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(pillX, pillY, pillW, pillH, 3);
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
      <div className="pointer-events-none absolute bottom-2.5 left-2.5 z-20 flex flex-wrap gap-2.5 rounded-lg border border-slate-200/90 bg-white/90 px-3 py-1.5 backdrop-blur-md text-[10px] text-slate-700 shadow-sm">
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
