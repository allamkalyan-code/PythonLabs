/**
 * App — root layout: sidebar + chat + optional tracker panel.
 */

import { useState } from "react"
import { LayoutGrid } from "lucide-react"
import { Chat } from "@/components/Chat"
import { ProjectSidebar } from "@/components/ProjectSidebar"
import { TrackerPanel } from "@/components/TrackerPanel"
import { useProject } from "@/hooks/useProject"

export default function App() {
  const { projects, selectedProject, loading, createProject, deleteProject, selectProject } = useProject()
  const [showTracker, setShowTracker] = useState(false)
  const [trackerVersion, setTrackerVersion] = useState(0)

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* Left sidebar */}
      <ProjectSidebar
        projects={projects}
        selectedProject={selectedProject}
        loading={loading}
        onSelect={selectProject}
        onCreate={async (...args) => { await createProject(...args) }}
        onDelete={deleteProject}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-indigo-400">✦</span>
            <span className="text-sm font-semibold text-gray-200">Maaya</span>
            {selectedProject && (
              <>
                <span className="text-gray-700">·</span>
                <span className="text-sm text-gray-400">{selectedProject.name}</span>
              </>
            )}
          </div>
          {selectedProject && (
            <button
              onClick={() => setShowTracker((v) => !v)}
              title="Toggle tracker panel"
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
                showTracker
                  ? "bg-indigo-600/30 text-indigo-300"
                  : "text-gray-600 hover:text-gray-300 hover:bg-gray-800"
              }`}
            >
              <LayoutGrid size={13} />
              <span>Tracker</span>
            </button>
          )}
        </div>

        {/* Chat + tracker */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 overflow-hidden">
            <Chat project={selectedProject} onTrackerUpdate={setTrackerVersion} />
          </div>
          {showTracker && selectedProject && (
            <TrackerPanel
              projectId={selectedProject.id}
              trackerVersion={trackerVersion}
              onClose={() => setShowTracker(false)}
            />
          )}
        </div>
      </div>
    </div>
  )
}
