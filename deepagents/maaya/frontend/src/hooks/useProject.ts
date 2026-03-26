/**
 * useProject — project CRUD state management.
 */

import { useCallback, useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { Project } from "@/types"

export function useProject() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const list = await api.listProjects()
      setProjects(list)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const createProject = useCallback(async (name: string, path: string, model: string) => {
    const project = await api.createProject(name, path, model)
    setProjects((prev) => [project, ...prev])
    setSelectedProject(project)
    return project
  }, [])

  const deleteProject = useCallback(async (id: number) => {
    await api.deleteProject(id)
    setProjects((prev) => prev.filter((p) => p.id !== id))
    if (selectedProject?.id === id) {
      setSelectedProject(null)
    }
  }, [selectedProject])

  const selectProject = useCallback((project: Project | null) => {
    setSelectedProject(project)
  }, [])

  return {
    projects,
    selectedProject,
    loading,
    refresh,
    createProject,
    deleteProject,
    selectProject,
  }
}
