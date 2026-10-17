"use client";

import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { ApiStatusBanner } from "../components/ApiStatusBanner";
import { AskBrainTab, ChatMessage } from "../components/AskBrainTab";
import { MutatorTab } from "../components/MutatorTab";
import { MemoryTab } from "../components/MemoryTab";
import { ForceGraph } from "../components/ForceGraph";
import { TraceDrawer } from "../components/TraceDrawer";
import { PERSONAS, PRESETS, PresetScenario } from "../lib/presets";
import {
  AgentTrace,
  MutateRequest,
  MutateResponse,
  Persona,
  StatsResponse,
  Subgraph,
} from "../lib/types";
import { api } from "../lib/api";
import { MessageSquare, Zap, Brain } from "lucide-react";

export default function Home() {
  const [selectedPersona, setSelectedPersona] = useState<Persona>(PERSONAS[0]); // default Meera
  const [activeTab, setActiveTab] = useState<"ask" | "mutate" | "memory">("ask");

  // Per-persona message history
  const [messagesByPersona, setMessagesByPersona] = useState<
    Record<string, ChatMessage[]>
  >({
    meera: [],
    kabir: [],
    riya: [],
  });

  // Current visual graph & telemetry
  const [subgraph, setSubgraph] = useState<Subgraph>({ nodes: [], edges: [] });
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);

  // Status flags
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 1. Initial Health Check & Cold Start Handler
  useEffect(() => {
    let attempts = 0;
    const checkHealth = async () => {
      try {
        const _health = await api.checkHealth();
        setIsWakingUp(false);
        fetchStats();
      } catch (_err) {
        attempts += 1;
        if (attempts <= 3) {
          setIsWakingUp(true);
          setTimeout(checkHealth, 5000);
        } else {
          setIsWakingUp(false);
          setErrorMessage("API server is currently unreachable. Operating in fallback mode.");
        }
      }
    };
    checkHealth();
  }, []);

  // 2. Periodic stats polling (every 15s)
  const fetchStats = async () => {
    try {
      const res = await api.getStats(selectedPersona.id);
      setStats(res);
    } catch {
      // ignore transient poll errors
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, [selectedPersona.id]);

  // Handlers
  const handleSelectPersona = (p: Persona) => {
    setSelectedPersona(p);
  };

  const handleSendQuery = async (queryText: string) => {
    setIsLoading(true);
    setErrorMessage(null);

    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: queryText,
      timestamp: new Date().toISOString(),
    };

    setMessagesByPersona((prev) => ({
      ...prev,
      [selectedPersona.id]: [...(prev[selectedPersona.id] || []), userMsg],
    }));

    try {
      const res = await api.query(selectedPersona.id, queryText);

      const assistantMsg: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        timestamp: new Date().toISOString(),
      };

      setMessagesByPersona((prev) => ({
        ...prev,
        [selectedPersona.id]: [...(prev[selectedPersona.id] || []), assistantMsg],
      }));

      if (res.subgraph) {
        setSubgraph(res.subgraph);
      }
      if (res.agent_trace) {
        setTraces(res.agent_trace);
      }
      fetchStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Query failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPreset = (preset: PresetScenario) => {
    // If preset assigns a specific persona, switch automatically
    if (preset.personaId !== selectedPersona.id) {
      const p = PERSONAS.find((item) => item.id === preset.personaId);
      if (p) setSelectedPersona(p);
    }
    handleSendQuery(preset.query);
  };

  const handleMutate = async (payload: MutateRequest): Promise<MutateResponse> => {
    const res = await api.mutate(payload);
    if (res.subgraph) {
      setSubgraph(res.subgraph);
    }
    fetchStats();
    return res;
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await api.reset();
      setMessagesByPersona({ meera: [], kabir: [], riya: [] });
      setSubgraph({ nodes: [], edges: [] });
      setTraces([]);
      fetchStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Reset failed.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#080c16] text-slate-100 font-sans">
      {/* Top Header */}
      <Header
        selectedPersona={selectedPersona}
        onSelectPersona={handleSelectPersona}
        stats={stats}
        onReset={handleReset}
        isResetting={isResetting}
      />

      {/* Api Status Banners */}
      <ApiStatusBanner
        isWakingUp={isWakingUp}
        isMockMode={stats?.mode === "mock"}
        errorMessage={errorMessage}
        onDismissError={() => setErrorMessage(null)}
      />

      {/* Main Split-Pane Layout */}
      <main className="flex-1 p-3 md:p-4">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 h-full">
          {/* LEFT COLUMN: Tabs (45% width) */}
          <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/60 p-3 lg:col-span-5 h-[calc(100vh-100px)] overflow-hidden">
            {/* Tabs Navigation */}
            <div className="flex items-center gap-1 border-b border-slate-800 pb-2 mb-3">
              <button
                type="button"
                onClick={() => setActiveTab("ask")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                  activeTab === "ask"
                    ? "bg-sky-600/20 text-sky-400 border border-sky-500/40"
                    : "text-slate-400 hover:text-white hover:bg-slate-900"
                }`}
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Ask Company Brain</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("mutate")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                  activeTab === "mutate"
                    ? "bg-amber-600/20 text-amber-400 border border-amber-500/40"
                    : "text-slate-400 hover:text-white hover:bg-slate-900"
                }`}
              >
                <Zap className="h-3.5 w-3.5" />
                <span>Live Mutator</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("memory")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                  activeTab === "memory"
                    ? "bg-purple-600/20 text-purple-400 border border-purple-500/40"
                    : "text-slate-400 hover:text-white hover:bg-slate-900"
                }`}
              >
                <Brain className="h-3.5 w-3.5" />
                <span>Tenant Memory</span>
              </button>
            </div>

            {/* Tab Contents */}
            <div className="flex-1 overflow-hidden">
              {activeTab === "ask" && (
                <AskBrainTab
                  persona={selectedPersona}
                  messages={messagesByPersona[selectedPersona.id] || []}
                  isLoading={isLoading}
                  onSendQuery={handleSendQuery}
                  onSelectPreset={handleSelectPreset}
                />
              )}
              {activeTab === "mutate" && (
                <MutatorTab
                  persona={selectedPersona}
                  onMutate={handleMutate}
                  onGoToPreset2={() => {
                    setActiveTab("ask");
                    const p2 = PRESETS.find((p) => p.id === 2);
                    if (p2) handleSelectPreset(p2);
                  }}
                />
              )}
              {activeTab === "memory" && <MemoryTab persona={selectedPersona} />}
            </div>
          </div>

          {/* RIGHT COLUMN: Live Graph & Trace Drawer (55% width) */}
          <div className="flex flex-col gap-3 lg:col-span-7 h-[calc(100vh-100px)] overflow-hidden">
            {/* Top: Force Graph Canvas */}
            <div className="flex-1 min-h-[380px] rounded-xl border border-slate-800 bg-slate-950/60 p-2 overflow-hidden flex flex-col">
              <div className="flex items-center justify-between px-2 pb-1 text-xs">
                <span className="font-semibold text-slate-300">
                  🌐 Live FalkorDB Traversal Canvas
                </span>
                <span className="text-[11px] text-slate-500 font-mono">
                  Active: Green Glow 🟢 | Superseded: Crimson 🔴
                </span>
              </div>
              <div className="flex-1 w-full h-full">
                <ForceGraph subgraph={subgraph} />
              </div>
            </div>

            {/* Bottom: Agent Telemetry & Exact Cypher Drawer */}
            <div className="shrink-0">
              <TraceDrawer traces={traces} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
