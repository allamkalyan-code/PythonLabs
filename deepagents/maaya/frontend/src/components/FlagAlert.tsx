/**
 * FlagAlert — inline yellow warning banner shown when a subagent returns FLAGS.
 * Rendered as a system message in the chat feed.
 */

interface Props {
  agent: string
  content: string   // pre-formatted "⚠ Flags from <agent>: ..." string
}

export function FlagAlert({ agent, content }: Props) {
  return (
    <div className="mx-4 my-1 px-3 py-2 rounded-lg bg-yellow-950/30 border border-yellow-700/30 flex items-start gap-2">
      <span className="text-yellow-500 text-xs mt-0.5 shrink-0">⚠</span>
      <p className="text-xs text-yellow-400/80 leading-snug">{content}</p>
    </div>
  )
}
