/**
 * ProjectSidebar — lists all projects with status dots.
 * Includes a "New Project" form inline at the bottom.
 */

import { useState } from "react"
import { Plus, Trash2, FolderOpen, Loader2 } from "lucide-react"
import type { Project } from "@/types"

interface Props {
  projects: Project[]
  selectedProject: Project | null
  loading: boolean
  onSelect: (project: Project) => void
  onCreate: (name: string, path: string, model: string) => Promise<unknown>
  onDelete: (id: number) => Promise<void>
}

const MODELS = [
  { value: "anthropic:claude-sonnet-4-6", label: "Sonnet 4.6" },
  { value: "anthropic:claude-opus-4-6", label: "Opus 4.6" },
  { value: "anthropic:claude-haiku-4-5-20251001", label: "Haiku 4.5" },
]

export function ProjectSidebar({ projects, selectedProject, loading, onSelect, onCreate, onDelete }: Props) {
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState("")
  const [path, setPath] = useState("")
  const [model, setModel] = useState(MODELS[0].value)
  const [creating, setCreating] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)

  const handleCreate = async () => {
    if (!name.trim() || !path.trim()) return
    setCreating(true)
    try {
      await onCreate(name.trim(), path.trim(), model)
      setName("")
      setPath("")
      setModel(MODELS[0].value)
      setShowForm(false)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col h-full border-r border-gray-800 w-56 shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-gray-800">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Projects</span>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-800 text-gray-500 hover:text-gray-200 transition-colors"
          title="New project"
        >
          <Plus size={14} />
        </button>
      </div>

      {/* New project form */}
      {showForm && (
        <div className="p-3 border-b border-gray-800 space-y-2">
          <input
            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-indigo-500"
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-indigo-500"
            placeholder="Directory path"
            value={path}
            onChange={(e) => setPath(e.target.value)}
          />
          <select
            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-100 focus:outline-none focus:border-indigo-500"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            {MODELS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={creating || !name.trim() || !path.trim()}
              className="flex-1 py-1 rounded text-xs bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              {creating ? "Creating..." : "Create"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-2 py-1 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Project list */}
      <div className="flex-1 overflow-y-auto py-1">
        {loading && projects.length === 0 && (
          <div className="flex justify-center py-6">
            <Loader2 size={16} className="animate-spin text-gray-600" />
          </div>
        )}
        {!loading && projects.length === 0 && (
          <p className="text-xs text-gray-600 text-center py-6 px-3">
            No projects yet. Click + to create one.
          </p>
        )}
        {projects.map((project) => {
          const isSelected = selectedProject?.id === project.id
          return (
            <div key={project.id} className="group relative">
              {confirmDelete === project.id ? (
                <div className="px-3 py-2 text-xs space-y-1">
                  <p className="text-gray-400">Delete "{project.name}"?</p>
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        await onDelete(project.id)
                        setConfirmDelete(null)
                      }}
                      className="px-2 py-0.5 rounded bg-red-700 hover:bg-red-600 text-white transition-colors"
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => setConfirmDelete(null)}
                      className="px-2 py-0.5 rounded text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => onSelect(project)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-left transition-colors ${
                    isSelected
                      ? "bg-indigo-600/20 text-gray-100"
                      : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
                  }`}
                >
                  <FolderOpen size={13} className="shrink-0 text-gray-500" />
                  <span className="text-xs truncate flex-1">{project.name}</span>
                  {/* Status dot — green for now; Phase 2 will animate during runs */}
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0 opacity-60" />
                </button>
              )}
              {/* Trash icon — visible on hover */}
              {confirmDelete !== project.id && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setConfirmDelete(project.id)
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded text-gray-600 hover:text-red-400 hover:bg-gray-800 transition-all"
                  title="Delete project"
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
