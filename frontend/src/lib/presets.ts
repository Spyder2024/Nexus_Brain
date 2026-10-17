import { Persona } from "./types";

export interface PresetScenario {
  id: number;
  icon: string;
  shortTitle: string;
  fullTitle: string;
  personaId: "meera" | "kabir" | "riya";
  query: string;
  hint: string;
}

export const PERSONAS: Persona[] = [
  {
    id: "meera",
    name: "Meera",
    role: "Staff SRE On-Call",
    avatar: "🛡️",
  },
  {
    id: "kabir",
    name: "Kabir",
    role: "ML Platform Lead",
    avatar: "🧠",
  },
  {
    id: "riya",
    name: "Riya",
    role: "New Grad Hire",
    avatar: "🌱",
  },
];

export const PRESETS: PresetScenario[] = [
  {
    id: 1,
    icon: "🕵️",
    shortTitle: "Shadow Expert",
    fullTitle: "Hidden SME Discovery",
    personaId: "meera",
    query: "Who actually knows the most about auth-service outages, and what breaks if it goes down?",
    hint: "Identifies Kavya (person-19) over official lead Devon via 18 SEV-1 ticket resolutions and 26 PRs.",
  },
  {
    id: 2,
    icon: "📜",
    shortTitle: "Stale Kafka Doc",
    fullTitle: "Temporal Decision Flip",
    personaId: "riya",
    query: "Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-082?",
    hint: "Warns against outdated DOC-082; traces supersession chain to active ADR-051 (gRPC Streaming).",
  },
  {
    id: 3,
    icon: "💥",
    shortTitle: "4-Hop Blast",
    fullTitle: "Cascading Blast Radius",
    personaId: "meera",
    query: "What is the blast radius if redis-session-store experiences an OOM crash?",
    hint: "Traces 4-hop cascade across Auth, Billing, and Gateway, listing exact team leads to page.",
  },
  {
    id: 4,
    icon: "🧠",
    shortTitle: "CUDA Playbook",
    fullTitle: "Cross-Agent Memory",
    personaId: "kabir",
    query: "How do we resolve the recurring CUDA memory leak in ml-inference-worker?",
    hint: "Recalls prior incident INC-045 and retrieves verified playbook-003 shared across tenants.",
  },
  {
    id: 5,
    icon: "🚨",
    shortTitle: "Breaking API",
    fullTitle: "Undocumented Breaking Change",
    personaId: "meera",
    query: "Why did recommendation-service crash with a deserialization error after PR-398?",
    hint: "Links crash INC-250 to unreviewed protobuf DTO changes in PR-398 on user-profile-service.",
  },
];
