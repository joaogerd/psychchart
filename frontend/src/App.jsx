import { useState } from 'react'
import ChartPreview from './app/preview/ChartPreview'
import YamlEditor from './app/editor/YamlEditor'
import Presets from './app/editor/Presets'
import WorkspacePanel from './app/components/WorkspacePanel'
import { exportChartFile } from './app/api/client'
import { appendReadoutPointToYaml } from './app/utils/yamlDomain'

export default function App() {
  const [yaml, setYaml] = useState('chart:\n  t_min: 10\n  t_max: 40\nindexes:\n  - index: ITU')
  const [showYaml, setShowYaml] = useState(true)
  const [activePanel, setActivePanel] = useState('layers')
  const [readout, setReadout] = useState(null)

  const handleExport = async (format) => {
    const blob = await exportChartFile({ yaml, format, dpi: 300 })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `psychchart.${format}`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const handleAddPoint = () => {
    if (!readout) return
    setYaml(appendReadoutPointToYaml(yaml, readout))
  }

  return (
    <div className="workstation">
      <header className="topbar">
        <div>
          <div className="product-name">psychChart</div>
          <div className="product-caption">Interactive psychrometric analysis workspace</div>
        </div>
        <div className="topbar-actions">
          <button className="btn" onClick={() => setShowYaml(!showYaml)}>
            {showYaml ? 'Hide YAML' : 'Show YAML'}
          </button>
          <button className="btn" onClick={() => handleExport('png')}>Export PNG</button>
          <button className="btn" onClick={() => handleExport('svg')}>Export SVG</button>
        </div>
      </header>

      <aside className="left-rail panel">
        <div className="panel-header compact">
          <div className="panel-title">Workspace</div>
          <div className="subtitle">Projects, presets and data sources.</div>
        </div>
        <div className="section">
          <Presets setYaml={setYaml} />
        </div>
        <div className="section muted-card">
          <div className="section-title">Data import</div>
          <p className="small-text">CSV/Parquet import will appear here. The YAML remains the reproducible source of truth.</p>
          <button className="btn btn-full" disabled>Upload data</button>
        </div>
      </aside>

      <main className="chart-stage">
        <ChartPreview yaml={yaml} onReadout={setReadout} />
        {showYaml && (
          <div className="panel editor-drawer">
            <div className="toolbar">
              <div className="toolbar-title">YAML / JSON configuration</div>
              <div className="toolbar-note">Reproducible chart definition</div>
            </div>
            <YamlEditor yaml={yaml} setYaml={setYaml} />
          </div>
        )}
      </main>

      <aside className="right-rail panel">
        <div className="panel-tabs">
          <button className={activePanel === 'layers' ? 'tab active' : 'tab'} onClick={() => setActivePanel('layers')}>Layers</button>
          <button className={activePanel === 'readout' ? 'tab active' : 'tab'} onClick={() => setActivePanel('readout')}>Readout</button>
          <button className={activePanel === 'projects' ? 'tab active' : 'tab'} onClick={() => setActivePanel('projects')}>Projects</button>
        </div>

        {activePanel === 'layers' && (
          <div className="section">
            <div className="section-title">Chart layers</div>
            <label className="check-row"><input type="checkbox" defaultChecked /> Saturation curve</label>
            <label className="check-row"><input type="checkbox" defaultChecked /> Relative humidity</label>
            <label className="check-row"><input type="checkbox" defaultChecked /> Thermal indexes</label>
            <label className="check-row"><input type="checkbox" /> Operational zones</label>
            <div className="info-box">Use this panel to control isolines, overlays and index fields.</div>
          </div>
        )}

        {activePanel === 'readout' && (
          <div className="section">
            <div className="section-title">Point readout</div>
            <div className="metric-grid">
              <div className="metric-card"><span>T</span><strong>{readout?.T?.toFixed(1) ?? '--'} °C</strong></div>
              <div className="metric-card"><span>RH</span><strong>{readout?.RH_pct?.toFixed(0) ?? '--'} %</strong></div>
              <div className="metric-card"><span>ITU</span><strong>{readout?.ITU?.toFixed(1) ?? '--'}</strong></div>
              <div className="metric-card"><span>W</span><strong>{readout?.W?.toExponential(2) ?? '--'}</strong></div>
              <div className="metric-card"><span>Enthalpy</span><strong>{readout?.h?.toFixed(1) ?? '--'}</strong></div>
              <div className="metric-card"><span>Dew point</span><strong>{readout?.Tdp?.toFixed(1) ?? '--'} °C</strong></div>
            </div>
            <button className="btn btn-primary btn-full readout-action" disabled={!readout} onClick={handleAddPoint}>Add point to chart</button>
          </div>
        )}

        {activePanel === 'projects' && (
          <WorkspacePanel yaml={yaml} onLoad={setYaml} />
        )}
      </aside>
    </div>
  )
}
