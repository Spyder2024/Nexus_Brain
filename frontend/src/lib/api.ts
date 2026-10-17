import {
  HealthResponse,
  MemoryResponse,
  MutateRequest,
  MutateResponse,
  QueryResponse,
  StatsResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errBody: any = null;
      try {
        errBody = await res.json();
      } catch {
        // non-json response
      }

      const code = errBody?.error?.code || `HTTP_${res.status}`;
      const message =
        errBody?.error?.message ||
        (res.status === 409
          ? "Conflict: Target ADR is already superseded."
          : res.status === 503
          ? "Database is currently warming up or seeding. Please retry in a few seconds."
          : `Request failed with status ${res.status}`);

      throw new ApiError(code, message, res.status);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) {
      throw err;
    }
    if (err.name === "AbortError") {
      throw new ApiError("TIMEOUT", "Request timed out after 15 seconds.", 408);
    }
    throw new ApiError("NETWORK_ERROR", err.message || "Failed to connect to API.", 0);
  }
}

export const api = {
  checkHealth: async (): Promise<HealthResponse> => {
    return request<HealthResponse>("/api/v1/health");
  },

  getStats: async (userId: string = "meera"): Promise<StatsResponse> => {
    return request<StatsResponse>(`/api/v1/stats?user_id=${encodeURIComponent(userId)}`);
  },

  query: async (userId: string, queryText: string, sessionId: string = "sess_01"): Promise<QueryResponse> => {
    return request<QueryResponse>("/api/v1/query", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        query: queryText,
        session_id: sessionId,
      }),
    });
  },

  mutate: async (payload: MutateRequest): Promise<MutateResponse> => {
    return request<MutateResponse>("/api/v1/mutate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getMemory: async (userId: string): Promise<MemoryResponse> => {
    return request<MemoryResponse>(`/api/v1/memory/${encodeURIComponent(userId)}`);
  },

  reset: async (): Promise<{ reseeded: boolean; nodes: number; edges: number }> => {
    return request<{ reseeded: boolean; nodes: number; edges: number }>("/api/v1/reset", {
      method: "POST",
    });
  },
};
