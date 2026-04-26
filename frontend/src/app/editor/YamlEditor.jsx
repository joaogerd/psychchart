export default function YamlEditor({ yaml, setYaml }) {
  return (
    <textarea
      value={yaml}
      onChange={(e) => setYaml(e.target.value)}
      style={{
        width: '100%',
        height: '100%',
        padding: 10,
        fontFamily: 'monospace',
        fontSize: 14,
        border: '1px solid #ddd'
      }}
    />
  );
}
