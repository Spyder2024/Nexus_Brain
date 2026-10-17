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
    <div className="flex h-full flex-col gap-4 overflow-y-auto pr-1">
      <div className="rounded-lg border border-sky-900/50 bg-sky-950/20 p-3 text-xs text-sky-200">
        <div className="flex items-center gap-2 font-semibold text-sky-300">
          <Zap className="h-4 w-4 text-sky-400" />
          <span>Bi-Temporal Live Graph Evolution (Temporal Scribe)</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-300 leading-relaxed">
          Simulate a real-time architectural decision made in a Slack war-room.
          NexusBrain atomically invalidates the prior standard in FalkorDB and
          rewires active decision links.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Target ADR to Supersede
            </label>
            <input
              type="text"
              value={supersedesId}
              onChange={(e) => setSupersedesId(e.target.value)}
              className="w-full rounded border border-slate-800 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200 outline-none focus:border-sky-500"
              required
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Governed System
            </label>
            <input
              type="text"
              value={systemName}
              onChange={(e) => setSystemName(e.target.value)}
              className="w-full rounded border border-slate-800 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200 outline-none focus:border-sky-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 mb-1">
            New Active Decision Title
          </label>
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full rounded border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-slate-200 outline-none focus:border-sky-500"
            required
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 mb-1">
            Originating Slack Channel
          </label>
          <input
            type="text"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full rounded border border-slate-800 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200 outline-none focus:border-sky-500"
            required
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 mb-1">
            Architectural Rationale / Incident Context
          </label>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={3}
            className="w-full rounded border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-slate-200 outline-none focus:border-sky-500 font-mono text-[11px]"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg bg-sky-600 px-4 py-2 font-semibold text-white shadow transition-all hover:bg-sky-500 disabled:opacity-50 mt-1"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Mutating FalkorDB Knowledge State...</span>
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
        <div className="flex items-start gap-2 rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Mutation Conflict:</div>
            <div>{errorMsg}</div>
          </div>
        </div>
      )}

      {/* Success Receipt */}
      {lastResult && (
        <div className="flex flex-col gap-2 rounded-lg border border-emerald-900/60 bg-emerald-950/30 p-3 text-xs text-emerald-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              <span>Graph Mutated Successfully ({lastResult.latency_ms} ms)</span>
            </div>
            <span className="font-mono text-[10px] bg-emerald-900/60 px-2 py-0.5 rounded text-emerald-300">
              {lastResult.new_decision.id} (ACTIVE)
            </span>
          </div>

          <div className="text-[11px] text-slate-300">
            Created active decision <b className="text-white">[{lastResult.new_decision.id}]</b> and
            marked <b className="text-rose-400">[{lastResult.superseded_decision.id}]</b> as SUPERSEDED.
          </div>

          <div className="mt-1 rounded border border-slate-800 bg-black/60 p-2 font-mono text-[10px] text-sky-300">
            {lastResult.cypher_executed}
          </div>

          {/* Action Callout */}
          <button
            type="button"
            onClick={onGoToPreset2}
            className="flex items-center justify-center gap-1.5 rounded bg-emerald-600/30 border border-emerald-500/50 py-1.5 font-semibold text-emerald-200 hover:bg-emerald-600/50 transition-colors mt-1"
          >
            <span>👉 Return to Ask Brain & Re-run Preset #2</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};
