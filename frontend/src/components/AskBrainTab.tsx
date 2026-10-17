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
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          <Sparkles className="h-3 w-3 text-sky-400" />
          <span>1-Click Golden Demo Scenarios</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectPreset(p)}
              disabled={isLoading}
              title={p.hint}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/60 p-2 text-left text-xs transition-all hover:border-sky-500/50 hover:bg-slate-850 hover:shadow-sm disabled:opacity-50"
            >
              <span className="text-base shrink-0">{p.icon}</span>
              <div className="truncate">
                <div className="font-semibold text-slate-200 truncate">
                  {p.id}. {p.shortTitle}
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {p.fullTitle}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-[300px] max-h-[440px]">
        {messages.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 text-center p-4">
            <span className="text-2xl mb-1">{persona.avatar}</span>
            <div className="text-xs font-semibold text-slate-300">
              Logged in as {persona.name} ({persona.role})
            </div>
            <p className="mt-1 text-[11px] text-slate-500 max-w-xs">
              Click a preset scenario above or enter a question below to traverse
              the enterprise knowledge graph.
            </p>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col gap-1 text-xs ${
                m.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[92%] rounded-xl px-3.5 py-2.5 ${
                  m.role === "user"
                    ? "bg-sky-600 text-white rounded-br-sm"
                    : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-sm"
                }`}
              >
                {m.role === "user" ? (
                  <div>{m.content}</div>
                ) : (
                  <div className="prose prose-invert prose-xs max-w-none space-y-2">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Verified Citations Badge Shelf */}
              {m.citations && m.citations.length > 0 && (
                <div className="w-full pl-2 mt-1">
                  <div className="text-[10px] font-mono text-slate-400 mb-1 font-semibold">
                    Verified Graph Citations ({m.citations.length}):
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
          <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-300">
            <Loader2 className="h-4 w-4 animate-spin text-sky-400" />
            <span>Traversing FalkorDB company_brain multi-hop relationships...</span>
          </div>
        )}
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="relative mt-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask about systems, decisions, outages, or owners as ${persona.name}...`}
          disabled={isLoading}
          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3.5 py-2.5 pr-10 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-2 top-2 rounded p-1 text-slate-400 hover:text-sky-400 disabled:opacity-30"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
};
