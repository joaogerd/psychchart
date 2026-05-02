const DEFAULT_API_BASE_URL = import.meta.env.VITE_PSYCHCHART_API_URL || '/api';

async function readErrorMessage(response) {
  const fallback = `Request failed. HTTP ${response.status}`;
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

async function requestJson(path, options = {}, apiBaseUrl = DEFAULT_API_BASE_URL) {
  const response = await fetch(`${apiBaseUrl}${path}`, options);

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function renderChart({ yaml, format = 'png', dpi = 180, apiBaseUrl = DEFAULT_API_BASE_URL }) {
  return requestJson(
    '/render',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yaml, format, dpi }),
    },
    apiBaseUrl
  );
}

export async function exportChartFile({ yaml, format = 'png', dpi = 300, apiBaseUrl = DEFAULT_API_BASE_URL }) {
  const response = await fetch(`${apiBaseUrl}/render/file`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml, format, dpi }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function computeReadout({ T, RH_pct, pressure = 101325 }) {
  return requestJson('/readout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ T, RH_pct, pressure }),
  });
}

export async function listProjects() {
  return requestJson('/projects');
}

export async function createProject({ name, yaml }) {
  return requestJson('/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, yaml }),
  });
}

export async function updateProject({ id, name, yaml }) {
  return requestJson(`/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, yaml }),
  });
}

export async function deleteProject(id) {
  return requestJson(`/projects/${id}`, { method: 'DELETE' });
}

export function buildDataUrl(renderResponse) {
  return `data:${renderResponse.media_type};base64,${renderResponse.data_base64}`;
}
