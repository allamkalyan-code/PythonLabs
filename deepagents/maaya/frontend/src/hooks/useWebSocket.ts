/**
 * useWebSocket — manages the WebSocket connection for a project.
 *
 * Handles all server→client frame types and exposes sendMessage, stopStream,
 * respondHil, respondCheckpoint, and resetSession to callers.
 */

import { useCallback, useEffect, useRef, useState } from "react"
import { api, createChatSocket } from "@/lib/api"
import type {
  ChatMessage,
  CheckpointRequest,
  FileDelta,
  HandoffResult,
  HilRequest,
  RunStatus,
} from "@/types"

const HISTORY_DIVIDER: ChatMessage = {
  id: "history-divider",
  role: "system",
  content: "── Previous conversation ──",
  timestamp: new Date().toISOString(),
}

export function useWebSocket(projectId: number | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const [wsStatus, setWsStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected")
  const [runStatus, setRunStatus] = useState<RunStatus>("idle")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [agentStatus, setAgentStatus] = useState<{ agent: string; action: string } | null>(null)
  const [hilRequest, setHilRequest] = useState<HilRequest | null>(null)
  const [checkpointRequest, setCheckpointRequest] = useState<CheckpointRequest | null>(null)
  const [fileDelta, setFileDelta] = useState<FileDelta | null>(null)
  const [trackerVersion, setTrackerVersion] = useState(0)

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg])
  }, [])

  // Load history whenever project changes
  useEffect(() => {
    if (!projectId) {
      setMessages([])
      return
    }
    api.getMessages(projectId).then((msgs) => {
      // Always show persisted messages; add divider only when there are some
      // so the user can visually distinguish prior-session content from live output.
      setMessages(msgs.length > 0 ? [...msgs, HISTORY_DIVIDER] : [])
    }).catch(() => setMessages([]))
  }, [projectId])

  const connect = useCallback(() => {
    if (!projectId) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return

    setWsStatus("connecting")
    const ws = createChatSocket(
      projectId,
      (raw: unknown) => {
        const d = raw as Record<string, unknown>
        const type = d.type as string

        if (type === "start") {
          setRunStatus("running")
          setAgentStatus(null)
          setFileDelta(null)

        } else if (type === "done") {
          setRunStatus("idle")
          setAgentStatus(null)

        } else if (type === "agent_status") {
          setAgentStatus({
            agent: d.agent as string,
            action: d.action as string,
          })

        } else if (type === "token") {
          // Token-level streaming: append delta to last AI/inner message in place.
          // The server sends `role` ("maaya" = orchestrator, anything else = subagent).
          // Subagent tokens stream into a gray "inner" bubble; orchestrator tokens into white.
          const delta = d.delta as string
          const tokenRole = (d.role as string) || "maaya"
          const isInner = tokenRole !== "maaya"
          const streamId = isInner ? "streaming-inner" : "streaming"
          const streamMsgRole: ChatMessage["role"] = isInner ? "inner" : "ai"

          setMessages((prev) => {
            const last = prev[prev.length - 1]
            if (last && last.id === streamId) {
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + delta },
              ]
            }
            return [
              ...prev,
              {
                id: streamId,
                role: streamMsgRole,
                content: delta,
                timestamp: new Date().toISOString(),
                agent: isInner ? tokenRole : undefined,
              },
            ]
          })

        } else if (type === "inner") {
          // Finalized subagent response — replace in-progress inner streaming bubble
          setMessages((prev) => {
            const withoutInner = prev.filter((m) => m.id !== "streaming-inner")
            return [
              ...withoutInner,
              {
                id: crypto.randomUUID(),
                role: "inner" as ChatMessage["role"],
                content: d.content as string,
                timestamp: new Date().toISOString(),
                agent: d.role as string | undefined,
              },
            ]
          })

        } else if (type === "message") {
          const msg = d.data as {
            type: string
            content: string
            tool_calls?: ChatMessage["tool_calls"]
          }
          if (msg.type === "human") return
          // Finalize orchestrator streaming bubble; also clear any leftover inner bubble
          setMessages((prev) => {
            const withoutStreaming = prev.filter(
              (m) => m.id !== "streaming" && m.id !== "streaming-inner"
            )
            return [
              ...withoutStreaming,
              {
                id: crypto.randomUUID(),
                role: msg.type as ChatMessage["role"],
                content: msg.content,
                tool_calls: msg.tool_calls,
                timestamp: new Date().toISOString(),
              },
            ]
          })

        } else if (type === "task_complete") {
          addMessage({
            id: crypto.randomUUID(),
            role: "task_complete",
            content: "",
            timestamp: new Date().toISOString(),
            agent: d.agent as string | undefined,
            input_tokens: d.input_tokens as number | undefined,
            output_tokens: d.output_tokens as number | undefined,
            cost_usd: d.cost_usd as number | undefined,
          })

        } else if (type === "handoff") {
          addMessage({
            id: crypto.randomUUID(),
            role: "handoff",
            content: "",
            timestamp: new Date().toISOString(),
            handoff: d as unknown as HandoffResult,
          })

        } else if (type === "file_delta") {
          setFileDelta({
            path: d.path as string,
            content: d.content as string,
            op: d.op as "write" | "edit",
          })

        } else if (type === "hil_request") {
          setHilRequest({
            id: d.id as string,
            tool: d.tool as string,
            args: d.args as Record<string, unknown>,
          })

        } else if (type === "checkpoint") {
          setRunStatus("checkpoint")
          setCheckpointRequest({
            id: d.id as string,
            title: d.title as string,
            body: d.body as string,
            options: d.options as CheckpointRequest["options"],
          })

        } else if (type === "error") {
          addMessage({
            id: crypto.randomUUID(),
            role: "error",
            content: d.content as string,
            timestamp: new Date().toISOString(),
          })
          setRunStatus("error")

        } else if (type === "flags_alert") {
          addMessage({
            id: crypto.randomUUID(),
            role: "system",
            content: `⚠ Flags from ${d.agent as string}: ${(d.flags as string[]).join("; ")}`,
            timestamp: new Date().toISOString(),
          })
        } else if (type === "tracker_update") {
          setTrackerVersion((v) => v + 1)
        }
        // Ignore: ping (keepalive only)
      },
      () => {
        setWsStatus("disconnected")
        setRunStatus("idle")
        setAgentStatus(null)
      },
    )
    ws.onopen = () => setWsStatus("connected")
    wsRef.current = ws
  }, [projectId, addMessage])

  // Reconnect on project change
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWsStatus("disconnected")
      setRunStatus("idle")
      setHilRequest(null)
      setCheckpointRequest(null)
      setAgentStatus(null)
    }
    connect()
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      connect()
      return
    }
    addMessage({
      id: crypto.randomUUID(),
      role: "human",
      content,
      timestamp: new Date().toISOString(),
    })
    wsRef.current.send(JSON.stringify({ type: "message", content }))
  }, [connect, addMessage])

  const stopStream = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: "stop" }))
  }, [])

  const respondHil = useCallback((id: string, approved: boolean) => {
    wsRef.current?.send(JSON.stringify({ type: "hil_response", id, approved }))
    setHilRequest(null)
  }, [])

  const respondCheckpoint = useCallback((id: string, choice: string, feedback?: string) => {
    wsRef.current?.send(JSON.stringify({ type: "checkpoint_response", id, choice, feedback }))
    setCheckpointRequest(null)
    setRunStatus("running")
  }, [])

  const resetSession = useCallback(async () => {
    if (!projectId) return
    await api.resetSession(projectId)
    setMessages([])
    setRunStatus("idle")
    setHilRequest(null)
    setCheckpointRequest(null)
    setFileDelta(null)
    setAgentStatus(null)
  }, [projectId])

  return {
    wsStatus,
    runStatus,
    isStreaming: runStatus === "running",
    messages,
    agentStatus,
    hilRequest,
    checkpointRequest,
    fileDelta,
    trackerVersion,
    sendMessage,
    stopStream,
    respondHil,
    respondCheckpoint,
    resetSession,
    connect,
  }
}
