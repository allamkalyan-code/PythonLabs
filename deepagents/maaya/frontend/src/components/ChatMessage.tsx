/**
 * ChatMessage — renders a single message bubble.
 * Every bubble shows: [datetime · role] header above the content.
 */

import type { ChatMessage } from "@/types"

interface Props {
  message: ChatMessage
}

const ROLE_LABELS: Record<string, string> = {
  human: "You",
  ai: "Maaya",
  inner: "thinking",
  tool: "tool",
  system: "system",
  task_complete: "usage",
  error: "error",
  checkpoint: "checkpoint",
  handoff: "handoff",
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
  } catch {
    return ""
  }
}

function formatCost(usd: number): string {
  return usd < 0.001 ? `<$0.001` : `$${usd.toFixed(4)}`
}

export function ChatMessageItem({ message }: Props) {
  const { role, content, timestamp, tool_calls, handoff } = message
  const label = ROLE_LABELS[role] ?? role
  const time = formatTimestamp(timestamp)
  const isHuman = role === "human"

  // task_complete: token/cost summary row
  if (role === "task_complete") {
    const { agent, input_tokens, output_tokens, cost_usd } = message
    return (
      <div className="flex justify-center py-1">
        <span className="text-xs text-gray-600 font-mono">
          {agent && <span className="text-gray-500">{agent} · </span>}
          {input_tokens?.toLocaleString()} in / {output_tokens?.toLocaleString()} out
          {cost_usd !== undefined && (
            <span className="text-gray-500"> · {formatCost(cost_usd)}</span>
          )}
        </span>
      </div>
    )
  }

  // system / history divider — flag alerts use yellow styling
  if (role === "system") {
    if (content.startsWith("⚠")) {
      return (
        <div className="mx-4 my-1 px-3 py-2 rounded-lg bg-yellow-950/30 border border-yellow-700/30 flex items-start gap-2">
          <span className="text-yellow-500 text-xs mt-0.5 shrink-0">⚠</span>
          <p className="text-xs text-yellow-400/80 leading-snug">{content}</p>
        </div>
      )
    }
    return (
      <div className="flex justify-center py-2">
        <span className="text-xs text-gray-600">{content}</span>
      </div>
    )
  }

  // error
  if (role === "error") {
    return (
      <div className="mx-4 my-1 px-3 py-2 rounded-lg bg-red-950/40 border border-red-800/50">
        <p className="text-xs text-gray-500 mb-1">{time} · error</p>
        <p className="text-sm text-red-300 whitespace-pre-wrap">{content}</p>
      </div>
    )
  }

  // inner monolog — subagent thinking, shown collapsed and muted
  if (role === "inner") {
    const agentName = message.agent ?? "agent"
    const isStreaming = (message as { id?: string }).id === "streaming-inner"
    return (
      <details className="mx-4 my-0.5 group" open={isStreaming}>
        <summary className="cursor-pointer flex items-center gap-1.5 text-xs text-gray-700 hover:text-gray-500 list-none select-none">
          <span className="transition-transform group-open:rotate-90 text-gray-600">▸</span>
          <span className="italic text-gray-600">{agentName}</span>
          {isStreaming && <span className="text-gray-700">…</span>}
        </summary>
        <div className="mt-1 ml-3 px-3 py-2 rounded-lg border border-gray-800/40 bg-gray-950/30">
          <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed font-mono">
            {content}
          </p>
        </div>
      </details>
    )
  }

  // handoff — collapsible block
  if (role === "handoff" && handoff) {
    const statusColor: Record<string, string> = {
      DONE: "text-green-400",
      PARTIAL: "text-yellow-400",
      BLOCKED: "text-orange-400",
      FAILED: "text-red-400",
    }
    return (
      <details className="mx-4 my-1 px-3 py-2 rounded-lg bg-gray-900 border border-gray-800 text-xs">
        <summary className="cursor-pointer text-gray-500 list-none flex items-center gap-2">
          <span>{time} · <span className="text-gray-400">{handoff.agent}</span></span>
          <span className={`font-semibold ${statusColor[handoff.status] ?? "text-gray-400"}`}>
            {handoff.status}
          </span>
          <span className="text-gray-600 ml-1">{handoff.summary}</span>
        </summary>
        <div className="mt-2 space-y-1 text-gray-500">
          {handoff.files_created.length > 0 && (
            <p><span className="text-gray-400">Created:</span> {handoff.files_created.join(", ")}</p>
          )}
          {handoff.files_modified.length > 0 && (
            <p><span className="text-gray-400">Modified:</span> {handoff.files_modified.join(", ")}</p>
          )}
          {handoff.assumptions.length > 0 && (
            <p><span className="text-gray-400">Assumptions:</span> {handoff.assumptions.join("; ")}</p>
          )}
          {handoff.flags.length > 0 && (
            <p className="text-orange-400"><span className="text-gray-400">Flags:</span> {handoff.flags.join("; ")}</p>
          )}
          <p><span className="text-gray-400">Next:</span> {handoff.next_suggested}</p>
        </div>
      </details>
    )
  }

  // Normal message bubble
  const bubbleClass = isHuman
    ? "bg-indigo-600/20 border border-indigo-500/30"
    : "bg-gray-900 border border-gray-800"

  return (
    <div className={`mx-4 my-1 px-4 py-3 rounded-xl ${bubbleClass}`}>
      <p className="text-xs text-gray-500 mb-1.5">
        {time} · <span className="text-gray-400">{label}</span>
      </p>
      {content && (
        <p className="text-sm text-gray-100 whitespace-pre-wrap leading-relaxed">{content}</p>
      )}
      {tool_calls && tool_calls.length > 0 && (
        <div className="mt-2 space-y-1">
          {tool_calls.map((tc, i) => (
            <div key={i} className="text-xs font-mono text-gray-500 bg-gray-800/50 px-2 py-1 rounded">
              <span className="text-indigo-400">{tc.name}</span>
              {Object.keys(tc.args).length > 0 && (
                <span className="text-gray-600 ml-1">
                  {JSON.stringify(tc.args).slice(0, 120)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
