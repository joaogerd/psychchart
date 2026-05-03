import { useState } from 'react'
import { renderChart, buildDataUrl, computeReadout } from '../api/client'
import { getChartDomain } from '../utils/yamlDomain'

export default function ChartPreview({ yaml, onReadout }) {
  const [imageSrc, setImageSrc] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [marker, setMarker] = useState(null)

  const handleRender = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await renderChart({ yaml })
      setImageSrc(buildDataUrl(result))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = async (event) => {
    if (!imageSrc) return
    const rect = event.currentTarget.getBoundingClientRect()
    const xRatio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
    const yRatio = Math.min(Math.max((event.clientY - rect.top) / rect.height, 0), 1)
    const domain = getChartDomain(yaml)
    const T = domain.tMin + xRatio * (domain.tMax - domain.tMin)
    const RH_pct = domain.rhMax - yRatio * (domain.rhMax - domain.rhMin)
    setMarker({ x: xRatio * 100, y: yRatio * 100 })
    try {
      const readout = await computeReadout({ T, RH_pct, pressure: domain.pressure })
      onReadout?.(readout)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="panel preview-card">
      <div className="toolbar">
        <div>
          <div className="toolbar-title">Interactive psychrometric chart</div>
          <div className="toolbar-note">Render and select a region to inspect T/RH/ITU.</div>
        </div>
        <button className="btn btn-primary" onClick={handleRender} disabled={loading}>
          {loading ? 'Rendering…' : 'Render'}
        </button>
      </div>
      {error && <div className="error-box">{error}</div>}
      <div className="preview-body interactive-preview">
        {imageSrc ? (
          <div className="image-click-layer" onClick={handleSelect}>
            <img src={imageSrc} className="preview-image" />
            {marker && <div className="click-marker" style={{ left: `${marker.x}%`, top: `${marker.y}%` }} />}
          </div>
        ) : (
          <div className="empty-state">Render the chart, then select a point to compute a psychrometric readout.</div>
        )}
      </div>
    </div>
  )
}
