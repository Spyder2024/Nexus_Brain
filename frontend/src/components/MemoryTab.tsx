import React, { useEffect, useState } from "react";
import { MemoryResponse, Persona } from "../lib/types";
import { api } from "../lib/api";
import { Brain, Lock, Share2, Loader2, RefreshCw } from "lucide-react";

interface Props {
  persona: Persona;
}

export const MemoryTab: React.FC<Props> = ({ persona }) => {
  const [memory, setMemory] = useState<MemoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMemory = async () => {
    setIsLoading(true);
    try {
      const res = await api.getMemory(persona.id);
      setMemory(res);
    } catch (err) {
      console.error("Failed to fetch memory:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemory();
  }, [persona.id]);

  const rawTurns = memory?.turns || [];
  const visibleTurns = rawTurns.filter((t) =>
    Boolean(((t.content || (t as any).text) || "").trim())
  );

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto pr-1 text-xs">
      {/* Header Info */}
      <div
        className="flex items-center justify-between rounded-xl p-3 shadow-sm"
        style={{
          background: "rgba(124, 58, 237, 0.06)",
          border: "1px solid rgba(124, 58, 237, 0.2)",
        }}
      >
        <div className="flex items-center gap-2.5">
          <Brain className="h-4 w-4 text-purple-600" />
          <div>
            <div className="font-semibold text-purple-900">
              Isolated Tenant Memory:{" "}
              <span className="font-mono text-[11px] font-bold text-purple-700">
                memory_tenant_{persona.id}
              </span>
            </div>
            <div className="text-[11px] text-slate-500">
              FalkorDB multigraph isolation: Private chat turns, shared verified playbooks.
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={fetchMemory}
          className="rounded-lg p-1.5 transition-colors text-slate-500 hover:text-slate-900 hover:bg-slate-100"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center text-xs text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin mr-2 text-purple-600" />
          <span>Loading tenant memory…</span>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {/* Section 1: Private Episodic Turns */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-[11px] text-slate-500">
              <Lock className="h-3 w-3 text-amber-600" />
              <span>Private Episodic Session Turns ({visibleTurns.length})</span>
            </div>

            {visibleTurns.length === 0 ? (
              <div
                className="rounded-xl p-3 text-[11px] italic"
                style={{
                  background: "rgba(241, 245, 249, 0.5)",
                  border: "1px dashed rgba(15, 23, 42, 0.12)",
                  color: "#64748b",
                }}
              >
                No private conversation turns for {persona.name} yet. Private session history stays strictly isolated in{" "}
                <code className="text-slate-900 font-semibold">memory_tenant_{persona.id}</code>.
              </div>
            ) : (
              <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto">
                {visibleTurns.map((t, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col gap-0.5 rounded-xl p-2.5 text-[11px] shadow-sm"
                    style={{
                      background: "#ffffff",
                      border: "1px solid rgba(15, 23, 42, 0.08)",
                    }}
                  >
                    <div className="flex items-center justify-between font-mono text-[9px]">
                      <span className="uppercase font-semibold text-blue-600">
                        {t.role}
                      </span>
                      <span className="text-slate-400">
                        {new Date(t.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="line-clamp-2 mt-0.5 text-slate-800">
                      {t.content || (t as any).text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Shared Cross-Tenant Procedural Playbooks */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-[11px] text-slate-500">
              <Share2 className="h-3 w-3 text-emerald-600" />
              <span>
                Shared Verified Procedural Playbooks ({memory?.shared_playbooks?.length || 0})
              </span>
            </div>

            {memory?.shared_playbooks?.map((pb, idx) => (
              <div
                key={idx}
                className="flex flex-col gap-1.5 rounded-xl p-3 text-xs shadow-sm"
                style={{
                  background: "#ffffff",
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="font-mono font-bold text-emerald-700">
                    [{pb.id}]
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] font-mono">
                    <span
                      className="rounded-full px-2 py-0.5 font-semibold"
                      style={{
                        background: "rgba(16, 185, 129, 0.12)",
                        color: "#065f46",
                      }}
                    >
                      Success: {pb.success_count}x
                    </span>
                    {pb.verified_by && (
                      <span
                        className="rounded-full px-2 py-0.5"
                        style={{
                          background: "rgba(241, 245, 249, 0.9)",
                          color: "#475569",
                        }}
                      >
                        Verified by: {pb.verified_by}
                      </span>
                    )}
                  </div>
                </div>

                <div className="font-semibold text-slate-900">
                  {pb.trigger_signature}
                </div>

                <div className="mt-1 space-y-1">
                  <div className="text-[10px] font-mono text-slate-500">
                    Resolution Steps:
                  </div>
                  <ol className="list-decimal list-inside space-y-0.5 text-[11px] font-mono pl-1 text-slate-700">
                    {pb.resolution_steps.map((step, sIdx) => (
                      <li key={sIdx}>{step}</li>
                    ))}
                  </ol>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
