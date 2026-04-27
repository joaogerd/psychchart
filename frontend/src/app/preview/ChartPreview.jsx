import { useState } from 'react'
import { renderChart, buildDataUrl } from '../api/client'

export default function ChartPreview({ yaml }) {
  const [imageSrc, setImageSrc] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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

  return (
    <div className="panel preview-card">
      <div className="toolbar">
        <div className="toolbar-title">Preview</div>
        <button className="btn btn-primary" onClick={handleRender} disabled={loading}>
          {loading ? 'Rendering…' : 'Render'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="preview-body">
        {imageSrc ? (
          <img src={imageSrc} className="preview-image" />
        ) : (
          <div className="empty-state">
            Click "Render" to generate a chart preview.
          </div>
        )}
      </div>
    </div>
  )
}
