// Shared TypeScript types for Maaya v2

export type ProjectModel =
  | "anthropic:claude-sonnet-4-6"
  | "anthropic:claude-opus-4-6"
  | "anthropic:claude-haiku-4-5-20251001"
  | string

export interface Project {
  id: number
  name: string
  path: string
  model: ProjectModel
  created_at: string
  updated_at: string
}

// ------------------------------------------------------------------
// Chat messages
// ------------------------------------------------------------------

export type MessageRole =
  | "human"
  | "ai"
  | "inner"       // subagent internal monolog — shown collapsed and gray
  | "tool"
  | "system"
  | "task_complete"
  | "error"
  | "checkpoint"
  | "handoff"

export interface ToolCall {
  name: string
  args: Record<string, unknown>
}

export interface ChatMessage {
  /** Client-side UUID — not from DB */
  id: string
  role: MessageRole
  content: string
  tool_calls?: ToolCall[]
  /** ISO datetime string */
  timestamp: string
  // task_complete fields
  agent?: string
  input_tokens?: number
  output_tokens?: number
  cost_usd?: number
  // handoff fields
  handoff?: HandoffResult
}

// ------------------------------------------------------------------
// Tracker
// ------------------------------------------------------------------

export type Status = "not_started" | "wip" | "done" | "blocked"
export type Priority = "low" | "medium" | "high" | "critical"

export interface Task {
  id: number
  story_id: number
  title: string
  description: string | null
  status: Status
  priority: Priority
  assigned_agent: string | null
  file_path: string | null
  input_output_types: string | null
  notes: string | null
  parallel_group: number | null
  depends_on: number[]
  changed_files: string[]
  created_at: string
  updated_at: string
}

export interface Story {
  id: number
  epic_id: number
  title: string
  user_story: string | null
  acceptance_criteria: string[]
  status: Status
  priority: Priority
  story_points: number | null
  assigned_agent: string | null
  depends_on: number[]
  tasks: Task[]
  created_at: string
  updated_at: string
}

export interface Epic {
  id: number
  project_id: number
  title: string
  description: string | null
  success_criteria: string | null
  status: Status
  priority: Priority
  stories: Story[]
  created_at: string
  updated_at: string
}

export interface TrackerData {
  project_id: number
  epics: Epic[]
}

// ------------------------------------------------------------------
// WebSocket frames
// ------------------------------------------------------------------

export interface HilRequest {
  id: string
  tool: string
  args: Record<string, unknown>
}

export interface CheckpointRequest {
  id: string
  title: string
  body: string
  options: Array<{ label: string; value: string }>
}

export interface HandoffResult {
  agent: string
  status: "DONE" | "PARTIAL" | "BLOCKED" | "FAILED"
  summary: string
  files_created: string[]
  files_modified: string[]
  tests_written: boolean
  test_files: string[]
  assumptions: string[]
  flags: string[]
  next_suggested: string
}

export interface FileDelta {
  path: string
  content: string
  op: "write" | "edit"
}

export type RunStatus = "idle" | "running" | "checkpoint" | "error"
