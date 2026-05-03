export function readNumberFromYaml(yaml, key, fallback) {
  const pattern = new RegExp(`\\b${key}\\s*:\\s*(-?\\d+(?:\\.\\d+)?)`)
  const match = yaml.match(pattern)
  return match ? Number(match[1]) : fallback
}

export function getChartDomain(yaml) {
  return {
    tMin: readNumberFromYaml(yaml, 't_min', 10),
    tMax: readNumberFromYaml(yaml, 't_max', 40),
    rhMin: 0,
    rhMax: 100,
    pressure: readNumberFromYaml(yaml, 'pressure', 101325),
  }
}

export function appendReadoutPointToYaml(yaml, readout) {
  const point = [
    '  - t: ' + readout.T.toFixed(2),
    '    rh: ' + readout.RH.toFixed(4),
    '    label: "Clicked: T=' + readout.T.toFixed(1) + ' °C | RH=' + readout.RH_pct.toFixed(0) + '% | ITU=' + readout.ITU.toFixed(1) + '"',
    '    marker: corner_cross',
    '    color: "#111827"',
    '    size: 360',
    '    show_label: true',
  ].join('\n')

  if (/^points:\s*$/m.test(yaml)) {
    return yaml.trimEnd() + '\n' + point + '\n'
  }

  return yaml.trimEnd() + '\n\npoints:\n' + point + '\n'
}
