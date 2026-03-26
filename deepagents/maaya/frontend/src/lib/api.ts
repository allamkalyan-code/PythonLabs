/**
 * REST API client for Maaya v2.
 * All calls go to /api/* (served by the FastAPI backend).
 */

import axios from "axios"
import type {
  Project,
  ChatMessage,
  MessageRole,
  TrackerData,
} from "@/types"

const http = axios.create({ baseURL: "" })

// ------------------------------------------------------------------
// Raw API response types (snake_case from server)
// ------------------------------------------------------------------

interface RawMessage {
  id: number
  project_id: number
  role: MessageRole
  content: string
  metadata: Record<string, unknown> | null
  created_at: string
}

function rawToMessage(raw: RawMessage): ChatMessage {
  const meta = raw.metadata ?? {}
  return {
    id: crypto.randomUUID(),
    role: raw.role,
    content: raw.content,
    timestamp: raw.created_at,
    tool_calls: (meta.tool_calls as ChatMessage["tool_calls"]) ?? undefined,
    // "inner" messages store agent name in meta.role; handoff messages use meta.agent
    agent: (meta.agent as string) ?? (meta.role as string) ?? undefined,
    input_tokens: (meta.input_tokens as number) ?? undefined,
    output_tokens: (meta.output_tokens as number) ?? undefined,
    cost_usd: (meta.cost_usd as number) ?? undefined,
  }
}

// ------------------------------------------------------------------
// API surface
// ------------------------------------------------------------------

export const api = {
  // Projects
  createProject: (name: string, path: string, model: string): Promise<Project> =>
    http.post<Project>("/api/projects", { name, path, model }).then((r) => r.data),

  listProjects: (): Promise<Project[]> =>
    http.get<Project[]>("/api/projects").then((r) => r.data),

  getProject: (id: number): Promise<Project> =>
    http.get<Project>(`/api/projects/${id}`).then((r) => r.data),

  updateProject: (id: number, patch: { name?: string; model?: string }): Promise<Project> =>
    http.patch<Project>(`/api/projects/${id}`, patch).then((r) => r.data),

  deleteProject: (id: number): Promise<void> =>
    http.delete(`/api/projects/${id}`).then(() => undefined),

  // Chat history
  getMessages: (projectId: number): Promise<ChatMessage[]> =>
    http
      .get<RawMessage[]>(`/api/projects/${projectId}/messages`)
      .then((r) => r.data.map(rawToMessage)),

  // Session reset — clears chat history + LangGraph checkpointer
  resetSession: (projectId: number): Promise<void> =>
    http.post(`/api/projects/${projectId}/reset-session`).then(() => undefined),

  // Tracker
  getTracker: (projectId: number): Promise<TrackerData> =>
    http.get<TrackerData>(`/api/projects/${projectId}/tracker`).then((r) => r.data),
}

// ------------------------------------------------------------------
// WebSocket factory
// ------------------------------------------------------------------

export function createChatSocket(
  projectId: number,
  onMessage: (data: unknown) => void,
  onClose: () => void,
): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  const ws = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${projectId}`)
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data as string))
    } catch {
      // Ignore malformed frames
    }
  }
  ws.onclose = onClose
  ws.onerror = onClose
  return ws
}
