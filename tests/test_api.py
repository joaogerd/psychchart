from fastapi.testclient import TestClient

from psychchart.api.fastapi_app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_render_png():
    yaml = """
chart:
  t_min: 10
  t_max: 40
  y_min: 0.0
  y_max: 0.03
"""
    response = client.post("/render", json={"yaml": yaml, "format": "png"})
    assert response.status_code == 200
    data = response.json()
    assert "data_base64" in data


def test_render_file():
    yaml = """
chart:
  t_min: 10
  t_max: 40
  y_min: 0.0
  y_max: 0.03
"""
    response = client.post("/render/file", json={"yaml": yaml, "format": "png"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
