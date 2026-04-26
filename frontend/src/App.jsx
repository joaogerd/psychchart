import { useState } from 'react';

export default function App() {
  const [yaml, setYaml] = useState('chart:\n  t_min: 10\n  t_max: 40');
  const [img, setImg] = useState(null);

  const renderChart = async () => {
    const res = await fetch('http://localhost:8000/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yaml })
    });

    const data = await res.json();
    setImg(`data:${data.media_type};base64,${data.data_base64}`);
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <textarea
        style={{ width: '40%', padding: 10 }}
        value={yaml}
        onChange={(e) => setYaml(e.target.value)}
      />

      <div style={{ flex: 1, padding: 10 }}>
        <button onClick={renderChart}>Render</button>
        {img && <img src={img} style={{ width: '100%' }} />}
      </div>
    </div>
  );
}
