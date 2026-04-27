import { useState } from 'react'
import ChartPreview from './app/preview/ChartPreview'
import YamlEditor from './app/editor/YamlEditor'
import Presets from './app/editor/Presets'
import WorkspacePanel from './app/components/WorkspacePanel'

export default function App() {
  const [yaml, setYaml] = useState('chart:\n  t_min: 10\n  t_max: 40')

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Arial' }}>

      <div style={{ width: 260, padding: 12, borderRight: '1px solid #ccc', background: '#fafafa' }}>
        <h3>psychChart</h3>
        <Presets setYaml={setYaml} />
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

        <div style={{ flex: 2, padding: 10 }}>
          <ChartPreview yaml={yaml} />
        </div>

        <div style={{ flex: 1, padding: 10 }}>
          <YamlEditor yaml={yaml} setYaml={setYaml} />
        </div>

      </div>

      <WorkspacePanel yaml={yaml} onLoad={setYaml} />

    </div>
  )
}
