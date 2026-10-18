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

// Color tokens for node types
const TYPE_COLORS: Record<string, string> = {
  System: "#38bdf8", // Sky blue
  Person: "#a855f7", // Purple
  Team: "#ec4899", // Pink
  Ticket: "#f97316", // Orange
  PullRequest: "#6366f1", // Indigo
  SlackThread: "#eab308", // Yellow
  Document: "#06b6d4", // Cyan
  Decision: "#10b981", // Emerald (Active)
  Playbook: "#14b8a6", // Teal
  TenantGraph: "#818cf8",
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
        className="flex h-full min-h-[380px] w-full flex-col items-center justify-center rounded-xl border border-white/5 bg-[#050811]/80 p-6 text-center"
      >
        <div className="text-3xl mb-2 opacity-80">🌐</div>
        <p className="text-sm font-medium text-slate-300">
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
      className="relative h-full min-h-[380px] w-full overflow-hidden rounded-xl border border-white/5 bg-[#050811]"
    >
      {/* Floating HUD Controls (Top-Right) */}
      <div className="absolute top-2.5 right-2.5 z-20 flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/60 p-1 backdrop-blur-md shadow-lg">
        <span className="px-2 font-mono text-[10px] text-slate-400 border-r border-white/10 select-none">
          {nodes.length} nodes · {edges.length} edges
        </span>
        <button
          type="button"
          onClick={handleZoomIn}
          title="Zoom In"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-300 hover:bg-white/10 hover:text-white transition"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          title="Zoom Out"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-300 hover:bg-white/10 hover:text-white transition"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={handleRecenter}
          title="Fit & Recenter Graph"
          className="flex h-6 w-6 items-center justify-center rounded text-slate-300 hover:bg-white/10 hover:text-white transition"
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
              ? "#ef4444"
              : status === "outdated"
              ? "#f59e0b"
              : TYPE_COLORS[node.type] || "#94a3b8";

          // 1. Halo / Glow Ring for Special Statuses
          if (status === "active" && node.type === "Decision") {
            ctx.save();
            ctx.shadowColor = "rgba(16, 185, 129, 0.7)";
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#10b981";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
          } else if (status === "superseded") {
            ctx.save();
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 2.5, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#ef4444";
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
          ctx.strokeStyle = "rgba(255, 255, 255, 0.45)";
          ctx.lineWidth = 1.2;
          ctx.stroke();

          // 3. Node Label Badge (Clean Pill Background to prevent text collisions)
          const rawLabel = String(node.label || node.id || "").trim();
          const displayLabel = rawLabel.length > 22 ? rawLabel.slice(0, 20) + "…" : rawLabel;

          // Keep font size clamped within readable bounds
          const fontSize = Math.min(Math.max(10 / globalScale, 6.5), 11);
          ctx.font = `500 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
          const textWidth = ctx.measureText(displayLabel).width;
          const pillPaddingX = 4.5;
          const pillPaddingY = 2;
          const pillH = fontSize + pillPaddingY * 2;
          const pillW = textWidth + pillPaddingX * 2;
          const pillX = node.x - pillW / 2;
          const pillY = node.y + r + 3;

          ctx.fillStyle = "rgba(9, 14, 26, 0.88)";
          ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
          ctx.lineWidth = 0.8;
          if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(pillX, pillY, pillW, pillH, 3.5);
            ctx.fill();
            ctx.stroke();
          } else {
            ctx.fillRect(pillX, pillY, pillW, pillH);
            ctx.strokeRect(pillX, pillY, pillW, pillH);
          }

          ctx.fillStyle = "#f8fafc";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(displayLabel, node.x, pillY + pillH / 2);
        }}
        linkColor={(link: any) =>
          link.relationship === "SUPERSEDES" ? "#f87171" : "#475569"
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

              ctx.fillStyle = "rgba(10, 15, 28, 0.92)";
              ctx.strokeStyle =
                rel === "SUPERSEDES"
                  ? "rgba(248, 113, 113, 0.5)"
                  : "rgba(255, 255, 255, 0.1)";
              ctx.lineWidth = 0.7;

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
                rel === "SUPERSEDES" ? "#f87171" : "#cbd5e1";
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillText(rel, textPos.x, textPos.y);
            }
          }
        }}
      />

      {/* Floating Legend (Bottom-Left) */}
      <div className="pointer-events-none absolute bottom-2.5 left-2.5 z-20 flex flex-wrap gap-2.5 rounded-lg border border-white/10 bg-black/65 px-3 py-1.5 backdrop-blur-md text-[10px] text-slate-300">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400 ring-2 ring-emerald-500/40" />
          Active ADR
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-rose-500 ring-2 ring-rose-500/40" />
          Superseded
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-sky-400" />
          System
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-purple-400" />
          Person
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-pink-400" />
          Team
        </span>
      </div>
    </div>
  );
};
