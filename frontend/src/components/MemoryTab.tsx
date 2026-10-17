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
    <div className="flex h-full flex-col gap-4 overflow-y-auto pr-1 text-xs">
      {/* Header Info */}
      <div className="flex items-center justify-between rounded-lg border border-purple-900/40 bg-purple-950/20 p-3">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-purple-400" />
          <div>
            <div className="font-semibold text-purple-300">
              Isolated Tenant Memory:{" "}
              <span className="font-mono text-purple-200">
                memory_tenant_{persona.id}
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              FalkorDB multigraph isolation: Private chat turns, shared verified playbooks.
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={fetchMemory}
          className="rounded p-1 text-slate-400 hover:text-white"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center text-slate-400">
          <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading tenant memory...
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Section 1: Private Episodic Turns */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
              <Lock className="h-3 w-3 text-amber-400" />
              <span>Private Episodic Session Turns ({memory?.turns?.length || 0})</span>
            </div>

            {!memory?.turns || memory.turns.length === 0 ? (
              <div className="rounded border border-dashed border-slate-800 p-3 text-[11px] text-slate-500 italic">
                No private conversation turns for {persona.name} yet. Private
                session history stays strictly isolated in{" "}
                <code>memory_tenant_{persona.id}</code>.
              </div>
            ) : (
              <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto">
                {memory.turns.map((t, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col gap-0.5 rounded border border-slate-800/80 bg-slate-900/50 p-2 text-[11px]"
                  >
                    <div className="flex items-center justify-between font-mono text-[9px] text-slate-400">
                      <span className="uppercase text-sky-400 font-semibold">
                        {t.role}
                      </span>
                      <span>{new Date(t.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-200 line-clamp-2">{t.content}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Shared Cross-Tenant Procedural Playbooks */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
              <Share2 className="h-3 w-3 text-emerald-400" />
              <span>
                Shared Verified Procedural Playbooks ({memory?.shared_playbooks?.length || 0})
              </span>
            </div>

            {memory?.shared_playbooks?.map((pb, idx) => (
              <div
                key={idx}
                className="flex flex-col gap-1.5 rounded-lg border border-emerald-900/60 bg-emerald-950/20 p-3 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="font-mono font-bold text-emerald-300">
                    [{pb.id}]
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
                    <span className="rounded bg-emerald-900/50 px-1.5 py-0.5">
                      Success: {pb.success_count}x
                    </span>
                    {pb.verified_by && (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">
                        Verified by: {pb.verified_by}
                      </span>
                    )}
                  </div>
                </div>

                <div className="font-semibold text-slate-200">
                  {pb.trigger_signature}
                </div>

                <div className="mt-1 space-y-1">
                  <div className="text-[10px] font-mono text-slate-400">
                    Resolution Steps:
                  </div>
                  <ol className="list-decimal list-inside space-y-0.5 text-[11px] text-slate-300 font-mono pl-1">
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
