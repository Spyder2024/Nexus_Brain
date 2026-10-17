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
    <div
      className="flex min-h-screen flex-col"
      style={{ background: "var(--bg-base)", color: "var(--text-primary)", fontFamily: "var(--font-geist-sans), system-ui, sans-serif" }}
    >
      {/* Ambient background layer */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 50% -10%, hsl(220, 80%, 18%) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 85% 85%, hsl(262, 60%, 16%) 0%, transparent 60%)
          `,
          zIndex: 0,
        }}
      />

      {/* Header */}
      <Header
        selectedPersona={selectedPersona}
        onSelectPersona={handleSelectPersona}
        stats={stats}
        onReset={handleReset}
        isResetting={isResetting}
      />

      {/* Status Banners */}
      <ApiStatusBanner
        isWakingUp={isWakingUp}
        isMockMode={stats?.mode === "mock"}
        errorMessage={errorMessage}
        onDismissError={() => setErrorMessage(null)}
      />

      {/* Main Split-Pane */}
      <main className="relative z-10 flex-1 p-3 md:p-4" style={{ minHeight: 0 }}>
        <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-12" style={{ height: "calc(100vh - 72px)" }}>

          {/* ── LEFT COLUMN (45%) ──────────────────────────────────── */}
          <div
            className="flex flex-col lg:col-span-5"
            style={{
              background: "rgba(255,255,255,0.025)",
              backdropFilter: "blur(32px) saturate(180%)",
              WebkitBackdropFilter: "blur(32px) saturate(180%)",
              border: "1px solid rgba(255,255,255,0.07)",
              borderRadius: "18px",
              overflow: "hidden",
            }}
          >
            {/* Tab Bar */}
            <div
              className="flex items-center gap-1 px-3 pt-3 pb-2.5 shrink-0"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              {(
                [
                  { key: "ask" as const,    label: "Ask Brain",     icon: <MessageSquare className="h-3.5 w-3.5" />, accent: "hsl(211,95%,60%)"   },
                  { key: "mutate" as const, label: "Live Mutator",  icon: <Zap className="h-3.5 w-3.5" />,           accent: "hsl(40,90%,60%)"    },
                  { key: "memory" as const, label: "Tenant Memory", icon: <Brain className="h-3.5 w-3.5" />,         accent: "hsl(262,80%,72%)"   },
                ] as const
              ).map((tab) => {
                const isActive = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-all duration-150"
                    style={{
                      background: isActive ? `${tab.accent}18` : "transparent",
                      color: isActive ? tab.accent : "rgba(255,255,255,0.4)",
                      border: isActive ? `1px solid ${tab.accent}30` : "1px solid transparent",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.75)";
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.4)";
                    }}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden p-3">
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

          {/* ── RIGHT COLUMN (55%) ─────────────────────────────────── */}
          <div className="flex flex-col gap-3 lg:col-span-7" style={{ minHeight: 0 }}>

            {/* Graph Canvas */}
            <div
              className="flex flex-1 flex-col overflow-hidden"
              style={{
                background: "rgba(255,255,255,0.025)",
                backdropFilter: "blur(32px) saturate(180%)",
                WebkitBackdropFilter: "blur(32px) saturate(180%)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: "18px",
                minHeight: "380px",
              }}
            >
              <div
                className="flex items-center justify-between px-4 py-3 shrink-0"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
              >
                <span
                  className="text-[12px] font-semibold"
                  style={{ color: "rgba(255,255,255,0.75)", letterSpacing: "-0.01em" }}
                >
                  Live FalkorDB Traversal Canvas
                </span>
                <div className="flex items-center gap-2 font-mono text-[11px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                  <span className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: "hsl(158,75%,55%)" }} />
                    Active
                  </span>
                  <span>·</span>
                  <span className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: "hsl(349,80%,65%)" }} />
                    Superseded
                  </span>
                </div>
              </div>
              <div className="flex-1 w-full" style={{ minHeight: 0 }}>
                <ForceGraph subgraph={subgraph} />
              </div>
            </div>

            {/* Trace Drawer */}
            <div className="shrink-0">
              <TraceDrawer traces={traces} />
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
