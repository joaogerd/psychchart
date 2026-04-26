export default function Presets({ setYaml }) {
  const presets = {
    Minimal: 'chart:\n  t_min: 10\n  t_max: 40',
    ITU: 'chart:\n  t_min: 10\n  t_max: 40\nindexes:\n  - index: ITU'
  };

  return (
    <div>
      <h4>Presets</h4>
      {Object.entries(presets).map(([name, yaml]) => (
        <button key={name} onClick={() => setYaml(yaml)} style={{ display: 'block', marginBottom: 6 }}>
          {name}
        </button>
      ))}
    </div>
  );
}
