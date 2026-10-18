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
        background: "rgba(6, 7, 13, 0.82)",
        backdropFilter: "blur(32px) saturate(200%)",
        WebkitBackdropFilter: "blur(32px) saturate(200%)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div
          className="flex h-9 w-9 items-center justify-center"
          style={{
            background: "linear-gradient(135deg, hsl(211,95%,55%), hsl(262,80%,65%))",
            borderRadius: "10px",
            boxShadow: "0 2px 12px hsla(211,95%,60%,0.4)",
          }}
        >
          <Hexagon className="h-5 w-5 text-white" strokeWidth={1.5} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1
              className="text-[15px] font-semibold tracking-tight text-white"
              style={{ letterSpacing: "-0.025em" }}
            >
              NexusBrain
            </h1>
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-widest uppercase"
              style={{
                background: "hsla(211,95%,60%,0.15)",
                color: "hsl(211,95%,72%)",
                border: "1px solid hsla(211,95%,60%,0.25)",
              }}
            >
              v2
            </span>
          </div>
          <p className="text-[11px]" style={{ color: "rgba(255,255,255,0.38)" }}>
            Graph-Native Enterprise Intelligence · FalkorDB
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Persona Selector */}
        <div
          className="flex items-center gap-2 px-3 py-2 text-xs"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "10px",
            backdropFilter: "blur(16px)",
          }}
        >
          <span className="text-base leading-none">{selectedPersona.avatar}</span>
          <select
            value={selectedPersona.id}
            onChange={(e) => {
              const p = PERSONAS.find((item) => item.id === e.target.value);
              if (p) onSelectPersona(p);
            }}
            className="bg-transparent font-medium outline-none cursor-pointer"
            style={{ color: "rgba(255,255,255,0.85)" }}
          >
            {PERSONAS.map((p) => (
              <option key={p.id} value={p.id} style={{ background: "#111628", color: "white" }}>
                {p.name} · {p.role}
              </option>
            ))}
          </select>
        </div>

        {/* Telemetry Badge */}
        <div
          className="flex items-center gap-2 px-3 py-2 font-mono text-[11px]"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "10px",
          }}
        >
          <span
            className="relative h-2 w-2 rounded-full shrink-0"
            style={{
              background: isMock
                ? "hsl(40, 90%, 60%)"
                : "hsl(158, 75%, 55%)",
              boxShadow: isMock
                ? "0 0 6px hsl(40, 90%, 60%)"
                : "0 0 6px hsl(158, 75%, 55%)",
            }}
          />
          <span style={{ color: "rgba(255,255,255,0.6)" }}>
            {stats ? `${stats.nodes} nodes · ${stats.edges} edges` : "Connecting…"}
          </span>
          {stats?.avg_query_ms !== undefined && (
            <span style={{ color: "hsl(158, 75%, 60%)", fontWeight: 600 }}>
              {stats.avg_query_ms.toFixed(1)}ms
            </span>
          )}
          {isMock && (
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
              style={{
                background: "hsla(349, 80%, 65%, 0.15)",
                color: "hsl(349, 80%, 70%)",
                border: "1px solid hsla(349, 80%, 65%, 0.3)",
              }}
            >
              Mock
            </span>
          )}
        </div>

        {/* Reset Button */}
        <button
          type="button"
          onClick={onReset}
          disabled={isResetting}
          title="Reset graph state to pristine Golden Scenarios"
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-all duration-150 disabled:opacity-40"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "10px",
            color: "rgba(255,255,255,0.65)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.08)";
            (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.9)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.04)";
            (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.65)";
          }}
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? "animate-spin" : ""}`} />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
};
