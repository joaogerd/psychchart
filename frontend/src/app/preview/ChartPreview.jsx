import { useState } from 'react';
import { renderChart, buildDataUrl } from '../api/client';

export default function ChartPreview({ yaml }) {
  const [imageSrc, setImageSrc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRender = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await renderChart({ yaml });
      setImageSrc(buildDataUrl(result));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: 8 }}>
        <button onClick={handleRender} disabled={loading}>
          {loading ? 'Rendering…' : 'Render chart'}
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: 8 }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, border: '1px solid #ddd', overflow: 'auto' }}>
        {imageSrc ? (
          <img src={imageSrc} style={{ width: '100%', display: 'block' }} />
        ) : (
          <div style={{ padding: 16, color: '#666' }}>
            Click "Render chart" to generate a preview.
          </div>
        )}
      </div>
    </div>
  );
}
