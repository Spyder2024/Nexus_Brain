import React, { useState } from "react";
import { MutateResponse, Persona } from "../lib/types";
import { Zap, CheckCircle2, AlertCircle, ArrowRight, Loader2 } from "lucide-react";

interface Props {
  persona: Persona;
  onMutate: (payload: {
    user_id: string;
    source_type: string;
    channel: string;
    system_name: string;
    new_decision_title: string;
    supersedes_decision_id: string;
    rationale: string;
  }) => Promise<MutateResponse>;
  onGoToPreset2: () => void;
}

export const MutatorTab: React.FC<Props> = ({
  persona,
  onMutate,
  onGoToPreset2,
}) => {
  const [supersedesId, setSupersedesId] = useState("ADR-051");
  const [newTitle, setNewTitle] = useState("Move auth-service RPC to HTTP/3 QUIC");
  const [channel, setChannel] = useState("#arch-sync");
  const [systemName, setSystemName] = useState("auth-service");
  const [rationale, setRationale] = useState(
    "In #arch-sync: Envoy proxy bug INC-299 causes gRPC stream resets under high concurrency. ADR-051 is hereby superseded; all new endpoints must adopt HTTP/3 QUIC."
  );

  const [isLoading, setIsLoading] = useState(false);
  const [lastResult, setLastResult] = useState<MutateResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await onMutate({
        user_id: persona.id,
        source_type: "SlackThread",
        channel,
        system_name: systemName,
        new_decision_title: newTitle,
        supersedes_decision_id: supersedesId,
        rationale,
      });
      setLastResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to mutate knowledge state.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto pr-1">
      {/* Overview Card */}
      <div
        className="rounded-xl p-3 text-xs shadow-sm"
        style={{
          background: "rgba(245, 158, 11, 0.08)",
          border: "1px solid rgba(245, 158, 11, 0.25)",
        }}
      >
        <div className="flex items-center gap-2 font-semibold" style={{ color: "#b45309" }}>
          <Zap className="h-4 w-4" />
          <span>Bi-Temporal Live Graph Evolution</span>
        </div>
        <p className="mt-1 text-[11px] leading-relaxed" style={{ color: "#78350f" }}>
          Simulate a real-time architectural decision made in a Slack war-room.
          NexusBrain atomically invalidates the prior standard in FalkorDB and rewires active decision links.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 mb-1">
              Target ADR to Supersede
            </label>
            <input
              type="text"
              value={supersedesId}
              onChange={(e) => setSupersedesId(e.target.value)}
              className="w-full rounded-lg px-3 py-2 font-mono text-[11px] outline-none transition-all duration-150 shadow-sm"
              style={{
                background: "#ffffff",
                border: "1px solid rgba(15, 23, 42, 0.12)",
                color: "#0f172a",
              }}
              required
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 mb-1">
              Governed System
            </label>
            <input
              type="text"
              value={systemName}
              onChange={(e) => setSystemName(e.target.value)}
              className="w-full rounded-lg px-3 py-2 font-mono text-[11px] outline-none transition-all duration-150 shadow-sm"
              style={{
                background: "#ffffff",
                border: "1px solid rgba(15, 23, 42, 0.12)",
                color: "#0f172a",
              }}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-700 mb-1">
            New Active Decision Title
          </label>
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full rounded-lg px-3 py-2 text-[12px] outline-none transition-all duration-150 shadow-sm"
            style={{
              background: "#ffffff",
              border: "1px solid rgba(15, 23, 42, 0.12)",
              color: "#0f172a",
            }}
            required
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-700 mb-1">
            Originating Slack Channel
          </label>
          <input
            type="text"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full rounded-lg px-3 py-2 font-mono text-[11px] outline-none transition-all duration-150 shadow-sm"
            style={{
              background: "#ffffff",
              border: "1px solid rgba(15, 23, 42, 0.12)",
              color: "#0f172a",
            }}
            required
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-700 mb-1">
            Architectural Rationale / Incident Context
          </label>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={3}
            className="w-full rounded-lg px-3 py-2 text-[11px] font-mono leading-relaxed outline-none transition-all duration-150 shadow-sm"
            style={{
              background: "#ffffff",
              border: "1px solid rgba(15, 23, 42, 0.12)",
              color: "#0f172a",
            }}
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 font-semibold text-white transition-all duration-150 disabled:opacity-40 mt-1"
          style={{
            background: "linear-gradient(135deg, hsl(38, 92%, 48%), hsl(25, 95%, 50%))",
            boxShadow: "0 2px 10px hsla(38, 92%, 48%, 0.3)",
          }}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Mutating FalkorDB Knowledge State…</span>
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              <span>⚡ Inject Decision into FalkorDB</span>
            </>
          )}
        </button>
      </form>

      {/* Error state */}
      {errorMsg && (
        <div
          className="flex items-start gap-2 rounded-xl p-3 text-xs shadow-sm"
          style={{
            background: "rgba(239, 68, 68, 0.08)",
            border: "1px solid rgba(239, 68, 68, 0.25)",
            color: "#991b1b",
          }}
        >
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Mutation Conflict:</div>
            <div>{errorMsg}</div>
          </div>
        </div>
      )}

      {/* Success Receipt */}
      {lastResult && (
        <div
          className="flex flex-col gap-2 rounded-xl p-3 text-xs shadow-sm"
          style={{
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            color: "#065f46",
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-semibold" style={{ color: "#065f46" }}>
              <CheckCircle2 className="h-4 w-4" />
              <span>Graph Mutated Successfully ({lastResult.latency_ms} ms)</span>
            </div>
            <span
              className="font-mono text-[10px] px-2 py-0.5 rounded-full font-bold"
              style={{
                background: "rgba(16, 185, 129, 0.2)",
                color: "#065f46",
              }}
            >
              {lastResult.new_decision.id} (ACTIVE)
            </span>
          </div>

          <div className="text-[11px] text-slate-700">
            Created active decision <b className="text-slate-900">[{lastResult.new_decision.id}]</b> and
            marked <b className="text-rose-600">[{lastResult.superseded_decision.id}]</b> as SUPERSEDED.
          </div>

          <div
            className="mt-1 rounded-lg p-2.5 font-mono text-[10px] overflow-x-auto shadow-sm"
            style={{
              background: "#f8fafc",
              border: "1px solid rgba(15, 23, 42, 0.08)",
              color: "#1e3a8a",
            }}
          >
            {lastResult.cypher_executed}
          </div>

          {/* Action Callout */}
          <button
            type="button"
            onClick={onGoToPreset2}
            className="flex items-center justify-center gap-1.5 rounded-lg py-2 font-semibold transition-all duration-150 mt-1 shadow-sm"
            style={{
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              color: "#065f46",
            }}
          >
            <span>👉 Return to Ask Brain & Re-run Preset #2</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};
