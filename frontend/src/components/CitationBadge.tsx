import React from "react";
import { Citation } from "../lib/types";

interface Props {
  citation: Citation;
}

export const CitationBadge: React.FC<Props> = ({ citation }) => {
  const status = (citation.status || "active").toLowerCase();
  const isActive = status === "active";
  const isSuperseded = status === "superseded";

  const borderColor = isActive
    ? "border-emerald-500/60 bg-emerald-950/40 text-emerald-300"
    : isSuperseded
    ? "border-rose-500/60 bg-rose-950/40 text-rose-300"
    : "border-amber-500/60 bg-amber-950/40 text-amber-300";

  const dotColor = isActive ? "bg-emerald-400" : isSuperseded ? "bg-rose-400" : "bg-amber-400";

  return (
    <div
      className={`flex flex-col gap-0.5 rounded border px-2.5 py-1.5 text-xs transition-colors ${borderColor}`}
    >
      <div className="flex items-center gap-1.5 font-mono font-semibold">
        <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
        <span>[{citation.id}]</span>
        <span className="text-[10px] uppercase opacity-75 font-normal tracking-wide">
          ({citation.label})
        </span>
      </div>
      <div className="line-clamp-1 text-[11px] opacity-90">{citation.title}</div>
      {citation.source_ref && (
        <div className="font-mono text-[9px] opacity-70">
          Source: {citation.source_ref}
        </div>
      )}
    </div>
  );
};
