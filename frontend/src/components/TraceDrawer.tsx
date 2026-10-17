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
        className="flex h-28 items-center justify-center rounded-2xl text-xs"
        style={{
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px dashed rgba(255, 255, 255, 0.08)",
          color: "rgba(255, 255, 255, 0.35)",
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
      className="flex flex-col gap-2 rounded-2xl p-3"
      style={{
        background: "rgba(255, 255, 255, 0.025)",
        backdropFilter: "blur(32px) saturate(180%)",
        WebkitBackdropFilter: "blur(32px) saturate(180%)",
        border: "1px solid rgba(255, 255, 255, 0.07)",
      }}
    >
      <div
        className="flex items-center justify-between pb-2"
        style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
      >
        <div className="flex items-center gap-2 text-xs font-semibold" style={{ color: "rgba(255, 255, 255, 0.75)" }}>
          <Terminal className="h-3.5 w-3.5" style={{ color: "hsl(211, 95%, 60%)" }} />
          <span>Multi-Agent Execution Trace ({traces.length} steps)</span>
        </div>
        <div
          className="flex items-center gap-1.5 font-mono text-[11px] font-semibold"
          style={{ color: "hsl(158, 75%, 60%)" }}
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
              className="rounded-xl overflow-hidden text-xs transition-colors"
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="flex w-full items-center justify-between px-3 py-2 text-left font-mono transition-colors"
              >
                <div className="flex items-center gap-2 truncate">
                  {isOpen ? (
                    <ChevronDown className="h-3 w-3 shrink-0" style={{ color: "rgba(255, 255, 255, 0.4)" }} />
                  ) : (
                    <ChevronRight className="h-3 w-3 shrink-0" style={{ color: "rgba(255, 255, 255, 0.4)" }} />
                  )}
                  <span className="font-semibold truncate" style={{ color: "hsl(262, 80%, 75%)" }}>
                    {trace.agent}
                  </span>
                  <span style={{ color: "rgba(255, 255, 255, 0.25)" }}>➔</span>
                  <span className="truncate" style={{ color: "hsl(211, 95%, 72%)" }}>
                    {trace.tool}
                  </span>
                </div>
                <span
                  className="text-[10px] shrink-0 font-medium font-mono"
                  style={{ color: "hsl(158, 75%, 65%)" }}
                >
                  {trace.latency_ms} ms
                </span>
              </button>

              {isOpen && (
                <div
                  className="p-2.5 font-mono text-[11px] leading-relaxed"
                  style={{
                    background: "rgba(0, 0, 0, 0.45)",
                    borderTop: "1px solid rgba(255, 255, 255, 0.05)",
                    color: "hsl(211, 90%, 75%)",
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

