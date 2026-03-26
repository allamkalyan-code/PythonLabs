/**
 * Chat — main chat panel with message feed, agent badge, and input.
 */

import { useEffect, useRef, useState, useCallback } from "react"
import { Send, Square, Wifi, WifiOff, Loader2, Bot, RotateCcw } from "lucide-react"
import { ChatMessageItem } from "./ChatMessage"
import type { Project } from "@/types"
import { useWebSocket } from "@/hooks/useWebSocket"

interface Props {
  project: Project | null
  onTrackerUpdate?: (version: number) => void
}

export function Chat({ project, onTrackerUpdate }: Props) {
  const {
    wsStatus,
    isStreaming,
    messages,
    agentStatus,
    hilRequest,
    checkpointRequest,
    fileDelta: _fileDelta,
    trackerVersion,
    sendMessage,
    stopStream,
    respondHil,
    respondCheckpoint,
    resetSession,
  } = useWebSocket(project?.id ?? null)

  // Bubble trackerVersion up to App so TrackerPanel can refresh
  useEffect(() => {
    onTrackerUpdate?.(trackerVersion)
  }, [trackerVersion, onTrackerUpdate])

  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, hilRequest, checkpointRequest, isStreaming])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    sendMessage(text)
    setInput("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 flex items-center justify-center">
          <span className="text-3xl">✦</span>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-100 mb-1">Hi, I'm Maaya</h2>
          <p className="text-sm text-gray-500 max-w-xs">
            Select or create a project in the sidebar to start building.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800 text-xs text-gray-500 shrink-0">
        {wsStatus === "connected" ? (
          <><Wifi size={12} className="text-green-400" /><span className="text-green-400">Connected</span></>
        ) : wsStatus === "connecting" ? (
          <><Loader2 size={12} className="animate-spin" /><span>Connecting...</span></>
        ) : (
          <><WifiOff size={12} className="text-red-400" /><span className="text-red-400">Disconnected</span></>
        )}

        {/* Active agent badge */}
        {agentStatus && (
          <>
            <span className="text-gray-700">·</span>
            <span className="text-indigo-400">▶ {agentStatus.agent}</span>
            <span className="text-gray-600">—</span>
            <span className="text-gray-400">{agentStatus.action}</span>
          </>
        )}
        {isStreaming && !agentStatus && (
          <>
            <span className="text-gray-700">·</span>
            <Loader2 size={11} className="animate-spin text-indigo-400" />
            <span className="text-indigo-400">Maaya is working...</span>
          </>
        )}

        {/* New Chat button */}
        <div className="ml-auto">
          <button
            onClick={resetSession}
            disabled={isStreaming}
            title="New chat — clears history and resets session"
            className="flex items-center gap-1 px-2 py-1 text-gray-600 hover:text-gray-300 hover:bg-gray-800 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <RotateCcw size={11} />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Message feed */}
      <div className="flex-1 overflow-y-auto py-2 space-y-0.5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-8 space-y-3">
            <Bot size={24} className="text-gray-600" />
            <div>
              <p className="text-sm text-gray-400">{project.name}</p>
              <p className="text-xs text-gray-600 mt-1">Tell me what you want to build.</p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessageItem key={msg.id} message={msg} />
        ))}

        {/* HIL approval card */}
        {hilRequest && (
          <div className="mx-4 my-2 p-4 rounded-xl bg-yellow-950/30 border border-yellow-700/40">
            <p className="text-xs text-yellow-400 font-semibold mb-1">Approval needed</p>
            <p className="text-sm text-gray-300 font-mono mb-1">{hilRequest.tool}</p>
            {Object.entries(hilRequest.args).slice(0, 3).map(([k, v]) => (
              <p key={k} className="text-xs text-gray-500 font-mono">
                <span className="text-gray-400">{k}:</span>{" "}
                {String(v).slice(0, 80)}
              </p>
            ))}
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => respondHil(hilRequest.id, true)}
                className="px-3 py-1 rounded text-xs bg-green-700 hover:bg-green-600 text-white transition-colors"
              >
                Approve
              </button>
              <button
                onClick={() => respondHil(hilRequest.id, false)}
                className="px-3 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
              >
                Reject
              </button>
            </div>
          </div>
        )}

        {/* Checkpoint card */}
        {checkpointRequest && (
          <div className="mx-4 my-2 p-4 rounded-xl bg-indigo-950/40 border border-indigo-600/40">
            <p className="text-sm font-semibold text-indigo-300 mb-2">{checkpointRequest.title}</p>
            <p className="text-sm text-gray-300 whitespace-pre-wrap mb-4">{checkpointRequest.body}</p>
            <div className="flex flex-wrap gap-2">
              {checkpointRequest.options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    if (opt.value === "request_changes") {
                      const feedback = window.prompt("What changes would you like?")
                      if (feedback) respondCheckpoint(checkpointRequest.id, opt.value, feedback)
                    } else {
                      respondCheckpoint(checkpointRequest.id, opt.value)
                    }
                  }}
                  className={`px-4 py-1.5 rounded text-sm transition-colors ${
                    opt.value === "approve"
                      ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                      : "bg-gray-800 hover:bg-gray-700 text-gray-300"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Streaming indicator */}
        {isStreaming && !agentStatus && (
          <div className="flex gap-3 px-4 py-2">
            <div className="flex items-center gap-1.5 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-4 shrink-0">
        <div className="flex gap-3 items-end bg-gray-900 border border-gray-700 rounded-xl p-3 focus-within:border-indigo-500/50 transition-colors">
          <textarea
            className="flex-1 bg-transparent text-sm text-gray-100 outline-none resize-none placeholder:text-gray-600 max-h-40"
            placeholder="Describe what you want to build..."
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              e.target.style.height = "auto"
              e.target.style.height = `${e.target.scrollHeight}px`
            }}
            onKeyDown={handleKeyDown}
            disabled={isStreaming || !!checkpointRequest}
          />
          {isStreaming ? (
            <button
              onClick={stopStream}
              className="w-8 h-8 rounded-lg bg-red-600 hover:bg-red-500 flex items-center justify-center transition-colors shrink-0"
              title="Stop"
            >
              <Square size={13} fill="currentColor" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim() || !!checkpointRequest}
              className="w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors shrink-0"
            >
              <Send size={13} />
            </button>
          )}
        </div>
        <p className="text-xs text-gray-700 mt-2 text-center">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  )
}
