import React from "react";
import { Persona, StatsResponse } from "../lib/types";
import { PERSONAS } from "../lib/presets";
import { RotateCcw, Zap } from "lucide-react";

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
    <header className="flex flex-col gap-3 border-b border-slate-800 bg-slate-950/80 px-4 py-3 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
          <Zap className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-white">
              NexusBrain
            </h1>
            <span className="rounded bg-sky-500/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-sky-300">
              v2.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Graph-Native Enterprise Intelligence & Multi-Agent Coordinator (FalkorDB)
          </p>
        </div>
      </div>

      {/* Controls: Persona + Telemetry + Reset */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Persona Selector */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1.5 text-xs">
          <span className="text-sm">{selectedPersona.avatar}</span>
          <select
            value={selectedPersona.id}
            onChange={(e) => {
              const p = PERSONAS.find((item) => item.id === e.target.value);
              if (p) onSelectPersona(p);
            }}
            className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer"
          >
            {PERSONAS.map((p) => (
              <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                {p.name} ({p.role})
              </option>
            ))}
          </select>
        </div>

        {/* Telemetry Badge */}
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-mono">
          <span
            className={`h-2 w-2 rounded-full ${
              isMock ? "bg-amber-400" : "bg-emerald-400 animate-pulse"
            }`}
          />
          <span className="text-slate-300">
            {stats ? `${stats.nodes} nodes | ${stats.edges} edges` : "Connecting..."}
          </span>
          {stats?.avg_query_ms !== undefined && (
            <span className="text-emerald-400 font-semibold">
              {stats.avg_query_ms.toFixed(1)}ms
            </span>
          )}
          {isMock && (
            <span className="rounded bg-rose-500/20 border border-rose-500/40 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-rose-300">
              Mock Data
            </span>
          )}
        </div>

        {/* Reset State Button */}
        <button
          type="button"
          onClick={onReset}
          disabled={isResetting}
          title="Reset graph state to pristine Golden Scenarios"
          className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? "animate-spin" : ""}`} />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
};
