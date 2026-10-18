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
        bg: "rgba(16, 185, 129, 0.08)",
        border: "rgba(16, 185, 129, 0.3)",
        text: "#065f46",
        dot: "#059669",
      }
    : isSuperseded
    ? {
        bg: "rgba(239, 68, 68, 0.08)",
        border: "rgba(239, 68, 68, 0.3)",
        text: "#991b1b",
        dot: "#dc2626",
      }
    : {
        bg: "rgba(245, 158, 11, 0.08)",
        border: "rgba(245, 158, 11, 0.3)",
        text: "#92400e",
        dot: "#d97706",
      };

  return (
    <div
      className="flex flex-col gap-0.5 rounded-xl px-3 py-2 text-xs transition-all duration-150 shadow-sm"
      style={{
        background: statusColors.bg,
        border: `1px solid ${statusColors.border}`,
        color: statusColors.text,
      }}
    >
      <div className="flex items-center gap-1.5 font-mono font-semibold">
        <span
          className="h-1.5 w-1.5 rounded-full shrink-0"
          style={{ background: statusColors.dot, boxShadow: `0 0 4px ${statusColors.dot}` }}
        />
        <span>[{citation.id}]</span>
        <span className="text-[10px] uppercase font-normal tracking-wide opacity-75">
          ({citation.label})
        </span>
      </div>
      <div className="line-clamp-1 text-[11px] font-medium text-slate-800">{citation.title}</div>
      {citation.source_ref && (
        <div className="font-mono text-[9px] text-slate-500 truncate">
          Source: {citation.source_ref}
        </div>
      )}
    </div>
  );
};
