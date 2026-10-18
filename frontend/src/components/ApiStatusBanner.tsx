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
      <div className="flex items-center gap-2.5 bg-sky-50 border-b border-sky-200 px-4 py-2 text-xs text-sky-800 shadow-sm">
        <Loader2 className="h-4 w-4 animate-spin text-sky-600 shrink-0" />
        <div>
          <span className="font-semibold">Waking up API server:</span> Render free
          tier spins down after inactivity. Resuming in ~20-30 seconds...
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="flex items-center justify-between bg-rose-50 border-b border-rose-200 px-4 py-2 text-xs text-rose-800 shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
        <button
          type="button"
          onClick={onDismissError}
          className="text-xs font-semibold underline text-rose-900 hover:text-rose-950"
        >
          Dismiss
        </button>
      </div>
    );
  }

  if (isMockMode) {
    return (
      <div className="flex items-center gap-2 bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-[11px] text-amber-900 font-mono shadow-sm">
        <Sparkles className="h-3 w-3 text-amber-600 shrink-0" />
        <span>
          MOCK MODE ACTIVE: Answers and graphs running on high-fidelity canned
          dataset. Start FalkorDB on port 6379 for live Cypher.
        </span>
      </div>
    );
  }

  return null;
};
