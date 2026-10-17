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
      <div className="flex h-32 items-center justify-center rounded-lg border border-slate-800 bg-slate-950/40 p-4 text-xs text-slate-500">
        Run a query to inspect real-time Cypher execution traces & latencies.
      </div>
    );
  }

  const toggle = (idx: number) => {
    setOpenIndexes((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const totalLatency = traces.reduce((acc, t) => acc + (t.latency_ms || 0), 0);

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-slate-800 bg-slate-950/70 p-3">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Terminal className="h-3.5 w-3.5 text-sky-400" />
          <span>Multi-Agent Execution Trace ({traces.length} steps)</span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
          <Cpu className="h-3 w-3" />
          <span>{totalLatency.toFixed(1)} ms total</span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto pr-1">
        {traces.map((trace, idx) => {
          const isOpen = openIndexes[idx] ?? false;
          return (
            <div
              key={idx}
              className="rounded border border-slate-800/60 bg-slate-900/40 text-xs overflow-hidden"
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="flex w-full items-center justify-between px-2.5 py-1.5 text-left font-mono hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center gap-2 truncate">
                  {isOpen ? (
                    <ChevronDown className="h-3 w-3 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-slate-400 shrink-0" />
                  )}
                  <span className="font-semibold text-purple-400 truncate">
                    {trace.agent}
                  </span>
                  <span className="text-slate-500">➔</span>
                  <span className="text-sky-300 truncate">{trace.tool}</span>
                </div>
                <span className="text-[10px] text-emerald-400 shrink-0 font-medium">
                  {trace.latency_ms} ms
                </span>
              </button>

              {isOpen && (
                <div className="border-t border-slate-800/80 bg-black/60 p-2.5 font-mono text-[11px] leading-relaxed text-sky-200">
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
