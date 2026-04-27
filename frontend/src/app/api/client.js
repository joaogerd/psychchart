const DEFAULT_API_BASE_URL = import.meta.env.VITE_PSYCHCHART_API_URL || '/api';

async function readErrorMessage(response) {
  const fallback = `Unable to render chart. HTTP ${response.status}`;
  const raw = await response.text();

  if (!raw) {
    return fallback;
  }

  try {
    const payload = JSON.parse(raw);
    return payload.detail || payload.message || raw;
  } catch {
    return raw;
  }
}

export async function renderChart({ yaml, format = 'png', dpi = 180, apiBaseUrl = DEFAULT_API_BASE_URL }) {
  const response = await fetch(`${apiBaseUrl}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml, format, dpi }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}

export function buildDataUrl(renderResponse) {
  return `data:${renderResponse.media_type};base64,${renderResponse.data_base64}`;
}
