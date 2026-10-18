import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Citation, Persona } from "../lib/types";
import { PRESETS, PresetScenario } from "../lib/presets";
import { CitationBadge } from "./CitationBadge";
import { Send, Sparkles, Loader2 } from "lucide-react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: string;
}

interface Props {
  persona: Persona;
  messages: ChatMessage[];
  isLoading: boolean;
  onSendQuery: (query: string) => void;
  onSelectPreset: (preset: PresetScenario) => void;
}

export const AskBrainTab: React.FC<Props> = ({
  persona,
  messages,
  isLoading,
  onSendQuery,
  onSelectPreset,
}) => {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendQuery(input.trim());
    setInput("");
  };

  return (
    <div className="flex h-full flex-col justify-between gap-3">

      {/* 5 One-Click Golden Demo Scenarios */}
      <div className="flex flex-col gap-2 shrink-0">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          <Sparkles className="h-3 w-3 text-blue-600" />
          <span>Golden Demo Scenarios</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectPreset(p)}
              disabled={isLoading}
              title={p.hint}
              className="flex items-center gap-2 rounded-xl p-2 text-left text-xs transition-all duration-150 disabled:opacity-40 shadow-sm"
              style={{
                background: "#ffffff",
                border: "1px solid rgba(15, 23, 42, 0.08)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "#f8fafc";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(37, 99, 235, 0.35)";
                (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 3px 10px rgba(15, 23, 42, 0.06)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "#ffffff";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(15, 23, 42, 0.08)";
                (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 1px 3px rgba(15, 23, 42, 0.03)";
              }}
            >
              <span className="text-base shrink-0">{p.icon}</span>
              <div className="truncate min-w-0">
                <div className="font-semibold truncate text-slate-900" style={{ fontSize: "11px" }}>
                  {p.id}. {p.shortTitle}
                </div>
                <div className="truncate text-[10px] text-slate-500">
                  {p.fullTitle}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1" style={{ minHeight: "200px" }}>
        {messages.length === 0 ? (
          <div
            className="flex h-48 flex-col items-center justify-center rounded-2xl text-center p-4"
            style={{
              background: "rgba(241, 245, 249, 0.6)",
              border: "1px dashed rgba(15, 23, 42, 0.12)",
            }}
          >
            <span className="text-3xl mb-2">{persona.avatar}</span>
            <div className="text-[12px] font-semibold text-slate-900">
              {persona.name} · {persona.role}
            </div>
            <p className="mt-1 text-[11px] max-w-xs text-slate-500 leading-relaxed">
              Choose a golden scenario above or ask anything about the enterprise knowledge graph.
            </p>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col gap-1 text-xs ${m.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className="max-w-[92%] rounded-2xl px-3.5 py-2.5"
                style={
                  m.role === "user"
                    ? {
                        background: "linear-gradient(135deg, hsl(221,83%,53%), hsl(225,80%,58%))",
                        color: "white",
                        borderBottomRightRadius: "5px",
                        boxShadow: "0 2px 8px hsla(221,83%,53%,0.25)",
                      }
                    : {
                        background: "#ffffff",
                        border: "1px solid rgba(15, 23, 42, 0.08)",
                        color: "#1e293b",
                        borderBottomLeftRadius: "5px",
                        boxShadow: "0 2px 10px rgba(15, 23, 42, 0.03)",
                      }
                }
              >
                {m.role === "user" ? (
                  <div style={{ fontSize: "12px", lineHeight: "1.6" }}>{m.content}</div>
                ) : (
                  <div className="prose-brain">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Citation Badges */}
              {m.citations && m.citations.length > 0 && (
                <div className="w-full pl-2 mt-1">
                  <div className="text-[10px] font-mono font-semibold mb-1 text-slate-500">
                    Verified Graph Citations ({m.citations.length})
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
                    {m.citations.map((c, idx) => (
                      <CitationBadge key={idx} citation={c} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div
            className="flex items-center gap-2.5 rounded-2xl p-3 text-xs"
            style={{
              background: "#ffffff",
              border: "1px solid rgba(15, 23, 42, 0.08)",
              color: "#475569",
              boxShadow: "0 2px 8px rgba(15, 23, 42, 0.03)",
            }}
          >
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            <span>Traversing FalkorDB company_brain multi-hop relationships…</span>
          </div>
        )}
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="relative mt-1 shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask ${persona.name} about systems, decisions, or owners…`}
          disabled={isLoading}
          className="w-full rounded-xl px-4 py-3 pr-11 text-[12px] outline-none transition-all duration-150"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(15, 23, 42, 0.12)",
            color: "#0f172a",
            caretColor: "hsl(221,83%,53%)",
            boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
          }}
          onFocus={(e) => {
            (e.currentTarget as HTMLInputElement).style.borderColor = "hsl(221,83%,53%)";
            (e.currentTarget as HTMLInputElement).style.boxShadow = "0 0 0 3px hsla(221,83%,53%,0.12)";
          }}
          onBlur={(e) => {
            (e.currentTarget as HTMLInputElement).style.borderColor = "rgba(15, 23, 42, 0.12)";
            (e.currentTarget as HTMLInputElement).style.boxShadow = "0 1px 3px rgba(15, 23, 42, 0.04)";
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-2.5 top-2.5 flex h-7 w-7 items-center justify-center rounded-lg transition-all duration-150 disabled:opacity-25"
          style={{
            background: "hsl(221,83%,53%)",
            color: "white",
            boxShadow: "0 1px 4px hsla(221,83%,53%,0.35)",
          }}
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </form>
    </div>
  );
};
