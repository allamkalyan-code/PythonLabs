/**
 * TrackerPanel — read-only Epic → Story → Task tree.
 * Refreshes whenever trackerVersion increments (triggered by tracker_update WS frames).
 */

import { useEffect, useState } from "react"
import { ChevronRight, X } from "lucide-react"
import { api } from "@/lib/api"
import type { Epic, Story, Task, TrackerData } from "@/types"

interface Props {
  projectId: number
  trackerVersion: number
  onClose: () => void
}

const STATUS_CHIP: Record<string, string> = {
  not_started: "bg-gray-800 text-gray-500",
  wip:         "bg-blue-900/60 text-blue-300",
  done:        "bg-green-900/50 text-green-400",
  blocked:     "bg-orange-900/50 text-orange-400",
}

const STATUS_LABEL: Record<string, string> = {
  not_started: "NOT STARTED",
  wip:         "WIP",
  done:        "DONE",
  blocked:     "BLOCKED",
}

function Chip({ status }: { status: string }) {
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${STATUS_CHIP[status] ?? "bg-gray-800 text-gray-600"}`}>
      {STATUS_LABEL[status] ?? status.toUpperCase()}
    </span>
  )
}

function TaskRow({ task }: { task: Task }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="ml-6 border-l border-gray-800 pl-3 py-0.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-start gap-1.5 w-full text-left hover:text-gray-300 transition-colors"
      >
        <ChevronRight
          size={11}
          className={`mt-0.5 shrink-0 text-gray-600 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <span className="text-xs text-gray-500 leading-snug flex-1">{task.title}</span>
        <Chip status={task.status} />
      </button>
      {open && (
        <div className="mt-1 ml-4 space-y-0.5 text-[11px] text-gray-600">
          {task.assigned_agent && (
            <p><span className="text-gray-500">agent:</span> {task.assigned_agent}</p>
          )}
          {task.file_path && (
            <p className="font-mono truncate" title={task.file_path}>
              <span className="text-gray-500">file:</span> {task.file_path}
            </p>
          )}
          {task.description && (
            <p className="text-gray-700 leading-snug">{task.description}</p>
          )}
        </div>
      )}
    </div>
  )
}

function StoryRow({ story }: { story: Story }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="ml-3 border-l border-gray-800 pl-3 py-0.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-start gap-1.5 w-full text-left hover:text-gray-200 transition-colors"
      >
        <ChevronRight
          size={11}
          className={`mt-0.5 shrink-0 text-gray-600 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <span className="text-xs text-gray-400 leading-snug flex-1">{story.title}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          {story.story_points && (
            <span className="text-[10px] text-gray-600">{story.story_points}pt</span>
          )}
          <Chip status={story.status} />
        </div>
      </button>
      {open && (
        <div className="mt-1 ml-4">
          {story.user_story && (
            <p className="text-[11px] text-gray-600 italic mb-1 leading-snug">{story.user_story}</p>
          )}
          {story.acceptance_criteria.length > 0 && (
            <ul className="text-[11px] text-gray-700 space-y-0.5 mb-1">
              {story.acceptance_criteria.map((ac, i) => (
                <li key={i} className="leading-snug">· {ac}</li>
              ))}
            </ul>
          )}
          {story.tasks.map((task) => (
            <TaskRow key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  )
}

function EpicRow({ epic }: { epic: Epic }) {
  const [open, setOpen] = useState(true)
  const totalPoints = epic.stories.reduce((s, st) => s + (st.story_points ?? 0), 0)
  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 transition-colors text-left"
      >
        <ChevronRight
          size={13}
          className={`shrink-0 text-gray-500 transition-transform ${open ? "rotate-90" : ""}`}
        />
        <span className="text-sm text-gray-200 font-medium flex-1 leading-snug">{epic.title}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[10px] text-gray-600">
            {epic.stories.length}s · {totalPoints}pt
          </span>
          <Chip status={epic.status} />
        </div>
      </button>
      {open && (
        <div className="px-2 py-1.5 space-y-0.5 bg-gray-950">
          {epic.stories.length === 0 ? (
            <p className="text-[11px] text-gray-700 px-2 py-1">No stories yet.</p>
          ) : (
            epic.stories.map((story) => (
              <StoryRow key={story.id} story={story} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

export function TrackerPanel({ projectId, trackerVersion, onClose }: Props) {
  const [data, setData] = useState<TrackerData | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch on mount, on tracker WS events, and every 3 s while open
  useEffect(() => {
    let cancelled = false

    const fetch = () => {
      api.getTracker(projectId)
        .then((d) => { if (!cancelled) setData(d) })
        .catch(() => { if (!cancelled) setData(null) })
        .finally(() => { if (!cancelled) setLoading(false) })
    }

    setLoading(true)
    fetch()
    const interval = setInterval(fetch, 3000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [projectId, trackerVersion])

  const totalStories = data?.epics.reduce((s, e) => s + e.stories.length, 0) ?? 0
  const totalPoints = data?.epics.reduce(
    (s, e) => s + e.stories.reduce((ss, st) => ss + (st.story_points ?? 0), 0),
    0,
  ) ?? 0

  return (
    <div className="w-80 flex flex-col h-full border-l border-gray-800 bg-gray-950">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-800 shrink-0">
        <div>
          <span className="text-sm font-semibold text-gray-200">Tracker</span>
          {data && data.epics.length > 0 && (
            <span className="ml-2 text-xs text-gray-600">
              {data.epics.length}e · {totalStories}s · {totalPoints}pt
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-600 hover:text-gray-300 transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {loading && (
          <p className="text-xs text-gray-600 text-center py-4">Loading...</p>
        )}
        {!loading && (!data || data.epics.length === 0) && (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <p className="text-xs text-gray-600">No epics yet.</p>
            <p className="text-[11px] text-gray-700 mt-1">
              The tracker fills in after the planner runs.
            </p>
          </div>
        )}
        {!loading && data && data.epics.map((epic) => (
          <EpicRow key={epic.id} epic={epic} />
        ))}
      </div>
    </div>
  )
}
