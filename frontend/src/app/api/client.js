const DEFAULT_API_BASE_URL = import.meta.env.VITE_PSYCHCHART_API_URL || '/api';

export async function renderChart({ yaml, format = 'png', dpi = 180, apiBaseUrl = DEFAULT_API_BASE_URL }) {
  const response = await fetch(`${apiBaseUrl}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml, format, dpi }),
  });

  if (!response.ok) {
    let message = 'Unable to render chart.';
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }

  return response.json();
}

export function buildDataUrl(renderResponse) {
  return `data:${renderResponse.media_type};base64,${renderResponse.data_base64}`;
}
