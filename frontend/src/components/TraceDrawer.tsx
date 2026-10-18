import React, { useState } from "react";
import { AgentTrace } from "../lib/types";
import { ChevronDown, ChevronRight, Terminal, Cpu } from "lucide-react";

interface Props {
  traces: AgentTrace[];
}

export const TraceDrawer: React.FC<Props> = ({ traces }) => {
  const [openIndexes, setOpenIndexes] = useState<Record<number, boolean>>({
    0: true,
  });

  if (!traces || traces.length === 0) {
    return (
      <div
        className="flex h-24 items-center justify-center rounded-2xl text-xs"
        style={{
          background: "rgba(241, 245, 249, 0.6)",
          border: "1px dashed rgba(15, 23, 42, 0.12)",
          color: "#64748b",
        }}
      >
        Run a query to inspect real-time Cypher execution traces & latencies.
      </div>
    );
  }

  const toggle = (idx: number) => {
    setOpenIndexes((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const totalLatency = traces.reduce((acc, t) => acc + (t.latency_ms || 0), 0);

  return (
    <div
      className="flex flex-col gap-2 rounded-2xl p-3 shadow-sm"
      style={{
        background: "rgba(255, 255, 255, 0.88)",
        backdropFilter: "blur(32px) saturate(180%)",
        WebkitBackdropFilter: "blur(32px) saturate(180%)",
        border: "1px solid rgba(15, 23, 42, 0.08)",
      }}
    >
      <div
        className="flex items-center justify-between pb-2"
        style={{ borderBottom: "1px solid rgba(15, 23, 42, 0.06)" }}
      >
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
          <Terminal className="h-3.5 w-3.5 text-blue-600" />
          <span>Multi-Agent Execution Trace ({traces.length} steps)</span>
        </div>
        <div
          className="flex items-center gap-1.5 font-mono text-[11px] font-semibold text-emerald-700"
        >
          <Cpu className="h-3 w-3" />
          <span>{totalLatency.toFixed(1)} ms total</span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 max-h-52 overflow-y-auto pr-1">
        {traces.map((trace, idx) => {
          const isOpen = openIndexes[idx] ?? false;
          return (
            <div
              key={idx}
              className="rounded-xl overflow-hidden text-xs transition-colors shadow-sm"
              style={{
                background: "#ffffff",
                border: "1px solid rgba(15, 23, 42, 0.08)",
              }}
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="flex w-full items-center justify-between px-3 py-2 text-left font-mono transition-colors hover:bg-slate-50"
              >
                <div className="flex items-center gap-2 truncate">
                  {isOpen ? (
                    <ChevronDown className="h-3 w-3 shrink-0 text-slate-400" />
                  ) : (
                    <ChevronRight className="h-3 w-3 shrink-0 text-slate-400" />
                  )}
                  <span className="font-semibold truncate text-purple-700">
                    {trace.agent}
                  </span>
                  <span className="text-slate-400">➔</span>
                  <span className="truncate text-blue-600 font-semibold">
                    {trace.tool}
                  </span>
                </div>
                <span
                  className="text-[10px] shrink-0 font-medium font-mono text-emerald-700"
                >
                  {trace.latency_ms} ms
                </span>
              </button>

              {isOpen && (
                <div
                  className="p-2.5 font-mono text-[11px] leading-relaxed"
                  style={{
                    background: "#f8fafc",
                    borderTop: "1px solid rgba(15, 23, 42, 0.06)",
                    color: "#1e3a8a",
                  }}
                >
                  <pre className="whitespace-pre-wrap break-all select-all font-mono">
                    {trace.cypher_executed}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
