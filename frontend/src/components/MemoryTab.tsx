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

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto pr-1 text-xs">
      {/* Header Info */}
      <div
        className="flex items-center justify-between rounded-xl p-3"
        style={{
          background: "hsla(262, 80%, 72%, 0.06)",
          border: "1px solid hsla(262, 80%, 72%, 0.15)",
        }}
      >
        <div className="flex items-center gap-2.5">
          <Brain className="h-4 w-4" style={{ color: "hsl(262, 80%, 72%)" }} />
          <div>
            <div className="font-semibold" style={{ color: "hsl(262, 80%, 75%)" }}>
              Isolated Tenant Memory:{" "}
              <span className="font-mono text-[11px]" style={{ color: "white" }}>
                memory_tenant_{persona.id}
              </span>
            </div>
            <div className="text-[11px]" style={{ color: "rgba(255, 255, 255, 0.4)" }}>
              FalkorDB multigraph isolation: Private chat turns, shared verified playbooks.
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={fetchMemory}
          className="rounded-lg p-1.5 transition-colors"
          style={{ color: "rgba(255,255,255,0.4)" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "white"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.4)"; }}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
          <Loader2 className="h-4 w-4 animate-spin mr-2" style={{ color: "hsl(262, 80%, 72%)" }} />
          <span>Loading tenant memory…</span>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {/* Section 1: Private Episodic Turns */}
          <div className="flex flex-col gap-2">
            <div
              className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-[11px]"
              style={{ color: "rgba(255,255,255,0.4)" }}
            >
              <Lock className="h-3 w-3" style={{ color: "hsl(40, 90%, 60%)" }} />
              <span>Private Episodic Session Turns ({memory?.turns?.length || 0})</span>
            </div>

            {!memory?.turns || memory.turns.length === 0 ? (
              <div
                className="rounded-xl p-3 text-[11px] italic"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px dashed rgba(255,255,255,0.08)",
                  color: "rgba(255,255,255,0.35)",
                }}
              >
                No private conversation turns for {persona.name} yet. Private session history stays strictly isolated in{" "}
                <code className="text-white">memory_tenant_{persona.id}</code>.
              </div>
            ) : (
              <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto">
                {memory.turns.map((t, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col gap-0.5 rounded-xl p-2.5 text-[11px]"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <div className="flex items-center justify-between font-mono text-[9px]">
                      <span className="uppercase font-semibold" style={{ color: "hsl(211, 95%, 72%)" }}>
                        {t.role}
                      </span>
                      <span style={{ color: "rgba(255,255,255,0.3)" }}>
                        {new Date(t.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="line-clamp-2 mt-0.5" style={{ color: "rgba(255,255,255,0.8)" }}>
                      {t.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Shared Cross-Tenant Procedural Playbooks */}
          <div className="flex flex-col gap-2">
            <div
              className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-[11px]"
              style={{ color: "rgba(255,255,255,0.4)" }}
            >
              <Share2 className="h-3 w-3" style={{ color: "hsl(158, 75%, 55%)" }} />
              <span>
                Shared Verified Procedural Playbooks ({memory?.shared_playbooks?.length || 0})
              </span>
            </div>

            {memory?.shared_playbooks?.map((pb, idx) => (
              <div
                key={idx}
                className="flex flex-col gap-1.5 rounded-xl p-3 text-xs"
                style={{
                  background: "hsla(158, 75%, 55%, 0.05)",
                  border: "1px solid hsla(158, 75%, 55%, 0.15)",
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="font-mono font-bold" style={{ color: "hsl(158, 75%, 65%)" }}>
                    [{pb.id}]
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] font-mono">
                    <span
                      className="rounded-full px-2 py-0.5 font-semibold"
                      style={{
                        background: "hsla(158, 75%, 55%, 0.15)",
                        color: "hsl(158, 75%, 70%)",
                      }}
                    >
                      Success: {pb.success_count}x
                    </span>
                    {pb.verified_by && (
                      <span
                        className="rounded-full px-2 py-0.5"
                        style={{
                          background: "rgba(255,255,255,0.06)",
                          color: "rgba(255,255,255,0.6)",
                        }}
                      >
                        Verified by: {pb.verified_by}
                      </span>
                    )}
                  </div>
                </div>

                <div className="font-semibold text-white/90">
                  {pb.trigger_signature}
                </div>

                <div className="mt-1 space-y-1">
                  <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Resolution Steps:
                  </div>
                  <ol className="list-decimal list-inside space-y-0.5 text-[11px] font-mono pl-1" style={{ color: "rgba(255,255,255,0.7)" }}>
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
