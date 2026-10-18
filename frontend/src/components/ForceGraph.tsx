"use client";

import React, { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Subgraph, SubgraphNode } from "../lib/types";

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
  const [dimensions, setDimensions] = useState({ width: 600, height: 420 });

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 600,
          height: containerRef.current.clientHeight || 420,
        });
      }
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  if (!subgraph?.nodes || subgraph.nodes.length === 0) {
    return (
      <div
        ref={containerRef}
        className="flex h-[420px] w-full flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-950/60 p-6 text-center"
      >
        <div className="text-3xl mb-2">🌐</div>
        <p className="text-sm font-medium text-slate-300">
          No active traversal subgraph
        </p>
        <p className="mt-1 text-xs text-slate-500 max-w-xs">
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
      className="relative h-[420px] w-full overflow-hidden rounded-lg border border-slate-800 bg-[#060911]"
    >
      {/* Visual Canvas */}
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel={(node: any) =>
          `${node.type}: ${node.label || node.id} (${node.status || "active"})`
        }
        nodeColor={(node: any) => {
          const status = (node.status || "active").toLowerCase();
          if (status === "superseded") return "#ef4444";
          if (status === "outdated") return "#f59e0b";
          return TYPE_COLORS[node.type] || "#94a3b8";
        }}
        nodeRelSize={7}
        nodeCanvasObjectMode={() => "after"}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = node.label || node.id;
          const fontSize = Math.max(10 / globalScale, 3.5);
          ctx.font = `${fontSize}px Inter, sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";

          // Glow ring for active decisions
          const status = (node.status || "active").toLowerCase();
          if (status === "active" && node.type === "Decision") {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#10b981";
            ctx.lineWidth = 2.5;
            ctx.stroke();
          } else if (status === "superseded") {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 7, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 2;
            ctx.stroke();
          }

          ctx.fillStyle = "#e2e8f0";
          ctx.fillText(label, node.x, node.y + 9);
        }}
        linkColor={(link: any) =>
          link.relationship === "SUPERSEDES" ? "#ef4444" : "#475569"
        }
        linkWidth={(link: any) =>
          link.relationship === "SUPERSEDES" ? 2.5 : 1.2
        }
        linkDirectionalArrowLength={4.5}
        linkDirectionalArrowRelPos={0.9}
        linkCanvasObjectMode={() => "after"}
        linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          if (link.relationship) {
            const start = link.source;
            const end = link.target;
            if (typeof start === "object" && typeof end === "object") {
              const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2,
              };
              const fontSize = Math.max(8 / globalScale, 2.5);
              ctx.font = `${fontSize}px JetBrains Mono, monospace`;
              ctx.fillStyle = link.relationship === "SUPERSEDES" ? "#f87171" : "#94a3b8";
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillText(link.relationship, textPos.x, textPos.y - 3);
            }
          }
        }}
        cooldownTicks={100}
      />

      {/* Floating Legend */}
      <div className="pointer-events-none absolute bottom-2 left-2 flex flex-wrap gap-2 rounded bg-black/80 px-2.5 py-1.5 backdrop-blur text-[10px] text-slate-300 border border-slate-800">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-emerald-400 ring-2 ring-emerald-500/50" />
          Active ADR
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-rose-500 ring-2 ring-rose-500/50" />
          Superseded
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-sky-400" /> System
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-purple-400" /> Person
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-pink-400" /> Team
        </span>
      </div>
    </div>
  );
};
