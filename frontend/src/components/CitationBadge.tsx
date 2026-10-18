import React from "react";
import { Citation } from "../lib/types";

interface Props {
  citation: Citation;
}

export const CitationBadge: React.FC<Props> = ({ citation }) => {
  const status = (citation.status || "active").toLowerCase();
  const isActive = status === "active";
  const isSuperseded = status === "superseded";

  const statusColors = isActive
    ? {
        bg: "hsla(158, 75%, 55%, 0.08)",
        border: "hsla(158, 75%, 55%, 0.2)",
        text: "hsl(158, 75%, 75%)",
        dot: "hsl(158, 75%, 55%)",
      }
    : isSuperseded
    ? {
        bg: "hsla(349, 80%, 65%, 0.08)",
        border: "hsla(349, 80%, 65%, 0.25)",
        text: "hsl(349, 80%, 75%)",
        dot: "hsl(349, 80%, 65%)",
      }
    : {
        bg: "hsla(40, 90%, 60%, 0.08)",
        border: "hsla(40, 90%, 60%, 0.2)",
        text: "hsl(40, 90%, 75%)",
        dot: "hsl(40, 90%, 60%)",
      };

  return (
    <div
      className="flex flex-col gap-0.5 rounded-xl px-3 py-2 text-xs transition-all duration-150"
      style={{
        background: statusColors.bg,
        border: `1px solid ${statusColors.border}`,
        color: statusColors.text,
      }}
    >
      <div className="flex items-center gap-1.5 font-mono font-semibold">
        <span
          className="h-1.5 w-1.5 rounded-full shrink-0"
          style={{ background: statusColors.dot, boxShadow: `0 0 6px ${statusColors.dot}` }}
        />
        <span>[{citation.id}]</span>
        <span className="text-[10px] uppercase font-normal tracking-wide opacity-60">
          ({citation.label})
        </span>
      </div>
      <div className="line-clamp-1 text-[11px] text-white/90">{citation.title}</div>
      {citation.source_ref && (
        <div className="font-mono text-[9px] opacity-50 truncate">
          Source: {citation.source_ref}
        </div>
      )}
    </div>
  );
};
