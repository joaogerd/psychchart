import { useEffect, useState } from 'react'
import { listProjects, createProject, deleteProject } from '../api/client'

export default function WorkspacePanel({ yaml, onLoad }) {
  const [projects, setProjects] = useState([])
  const [name, setName] = useState('')

  async function refresh() {
    const data = await listProjects()
    setProjects(data)
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleSave() {
    await createProject({ name, yaml })
    setName('')
    refresh()
  }

  async function handleDelete(id) {
    await deleteProject(id)
    refresh()
  }

  return (
    <div style={{ borderLeft: '1px solid #ddd', padding: 12, width: 300 }}>
      <h3>Projects</h3>

      <input
        placeholder="Project name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button onClick={handleSave}>Save</button>

      <ul>
        {projects.map((p) => (
          <li key={p.id}>
            <strong>{p.name}</strong>
            <br />
            <button onClick={() => onLoad(p.yaml)}>Load</button>
            <button onClick={() => handleDelete(p.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
