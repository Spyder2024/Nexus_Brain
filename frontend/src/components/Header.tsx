import React from "react";
import { Persona, StatsResponse } from "../lib/types";
import { PERSONAS } from "../lib/presets";
import { RotateCcw, Hexagon } from "lucide-react";

interface Props {
  selectedPersona: Persona;
  onSelectPersona: (p: Persona) => void;
  stats: StatsResponse | null;
  onReset: () => void;
  isResetting: boolean;
}

export const Header: React.FC<Props> = ({
  selectedPersona,
  onSelectPersona,
  stats,
  onReset,
  isResetting,
}) => {
  const isMock = stats?.mode === "mock";

  return (
    <header
      className="relative z-10 flex flex-col gap-3 px-5 py-3.5 sm:flex-row sm:items-center sm:justify-between"
      style={{
        background: "rgba(255, 255, 255, 0.88)",
        backdropFilter: "blur(32px) saturate(180%)",
        WebkitBackdropFilter: "blur(32px) saturate(180%)",
        borderBottom: "1px solid rgba(15, 23, 42, 0.08)",
        boxShadow: "0 2px 10px rgba(15, 23, 42, 0.03)",
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div
          className="flex h-9 w-9 items-center justify-center shadow-md"
          style={{
            background: "linear-gradient(135deg, hsl(221,83%,53%), hsl(262,72%,56%))",
            borderRadius: "10px",
            boxShadow: "0 2px 10px hsla(221,83%,53%,0.3)",
          }}
        >
          <Hexagon className="h-5 w-5 text-white" strokeWidth={1.5} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1
              className="text-[15px] font-semibold tracking-tight text-slate-900"
              style={{ letterSpacing: "-0.025em" }}
            >
              NexusBrain
            </h1>
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-widest uppercase"
              style={{
                background: "rgba(37, 99, 235, 0.08)",
                color: "#2563eb",
                border: "1px solid rgba(37, 99, 235, 0.2)",
              }}
            >
              v2
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            Graph-Native Enterprise Intelligence · FalkorDB
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Persona Selector */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 text-xs transition"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(15, 23, 42, 0.1)",
            borderRadius: "10px",
            boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
          }}
        >
          <span className="text-base leading-none">{selectedPersona.avatar}</span>
          <select
            value={selectedPersona.id}
            onChange={(e) => {
              const p = PERSONAS.find((item) => item.id === e.target.value);
              if (p) onSelectPersona(p);
            }}
            className="bg-transparent font-medium text-slate-800 outline-none cursor-pointer"
          >
            {PERSONAS.map((p) => (
              <option key={p.id} value={p.id} style={{ background: "#ffffff", color: "#0f172a" }}>
                {p.name} · {p.role}
              </option>
            ))}
          </select>
        </div>

        {/* Telemetry Badge */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 font-mono text-[11px]"
          style={{
            background: "rgba(241, 245, 249, 0.9)",
            border: "1px solid rgba(15, 23, 42, 0.08)",
            borderRadius: "10px",
            color: "#475569",
          }}
        >
          <span
            className="relative h-2 w-2 rounded-full shrink-0"
            style={{
              background: isMock
                ? "hsl(187, 85%, 43%)"
                : "hsl(158, 80%, 38%)",
              boxShadow: isMock
                ? "0 0 6px hsl(187, 85%, 43%)"
                : "0 0 6px hsl(158, 80%, 38%)",
            }}
          />
          <span className="font-medium">
            {stats ? `${stats.nodes} nodes · ${stats.edges} edges` : "Connecting…"}
          </span>
          {stats?.avg_query_ms !== undefined && (
            <span style={{ color: "hsl(158, 80%, 35%)", fontWeight: 600 }}>
              {stats.avg_query_ms.toFixed(1)}ms
            </span>
          )}
          {stats && (
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
              style={{
                background: isMock ? "rgba(6, 182, 212, 0.1)" : "rgba(16, 185, 129, 0.1)",
                color: isMock ? "#0891b2" : "#059669",
                border: isMock
                  ? "1px solid rgba(6, 182, 212, 0.25)"
                  : "1px solid rgba(16, 185, 129, 0.25)",
              }}
            >
              {isMock ? "SYNCED" : "LIVE"}
            </span>
          )}
        </div>

        {/* Reset Button */}
        <button
          type="button"
          onClick={onReset}
          disabled={isResetting}
          title="Reset graph state to pristine Golden Scenarios"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-150 disabled:opacity-40"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(15, 23, 42, 0.1)",
            borderRadius: "10px",
            color: "#475569",
            boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "#f8fafc";
            (e.currentTarget as HTMLButtonElement).style.color = "#0f172a";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "#ffffff";
            (e.currentTarget as HTMLButtonElement).style.color = "#475569";
          }}
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? "animate-spin" : ""}`} />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
};
