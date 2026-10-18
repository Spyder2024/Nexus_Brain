import React from "react";
import { AlertCircle, Loader2, Sparkles } from "lucide-react";

interface Props {
  isWakingUp: boolean;
  isMockMode: boolean;
  errorMessage: string | null;
  onDismissError: () => void;
}

export const ApiStatusBanner: React.FC<Props> = ({
  isWakingUp,
  isMockMode,
  errorMessage,
  onDismissError,
}) => {
  if (isWakingUp) {
    return (
      <div className="flex items-center gap-2.5 bg-sky-950/80 border-b border-sky-800/80 px-4 py-2 text-xs text-sky-200">
        <Loader2 className="h-4 w-4 animate-spin text-sky-400 shrink-0" />
        <div>
          <span className="font-semibold">Waking up API server:</span> Render free
          tier spins down after inactivity. Resuming in ~20-30 seconds...
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="flex items-center justify-between bg-rose-950/80 border-b border-rose-800/80 px-4 py-2 text-xs text-rose-200">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
        <button
          type="button"
          onClick={onDismissError}
          className="text-xs font-semibold underline hover:text-white"
        >
          Dismiss
        </button>
      </div>
    );
  }

  if (isMockMode) {
    return (
      <div className="flex items-center gap-2 bg-amber-950/40 border-b border-amber-900/50 px-4 py-1 text-[11px] text-amber-300 font-mono">
        <Sparkles className="h-3 w-3 text-amber-400 shrink-0" />
        <span>
          MOCK MODE ACTIVE: Answers and graphs running on high-fidelity canned
          dataset. Start FalkorDB on port 6379 for live Cypher.
        </span>
      </div>
    );
  }

  return null;
};
