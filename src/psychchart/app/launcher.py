"""Console launcher for the optional Streamlit app."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    """Launch the interactive Streamlit application."""
    try:
        from streamlit.web import bootstrap
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "The interactive app requires Streamlit. Install it with:\n"
            "  pip install -e .[app]"
        ) from exc

    app_path = Path(__file__).with_name("streamlit_app.py")
    bootstrap.run(str(app_path), False, [], {})


if __name__ == "__main__":
    main()
