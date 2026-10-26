import sys
from pathlib import Path
from streamlit.web import cli

sys.argv = ["streamlit", "run", str(Path(__file__).parent / "app.py")]
sys.exit(cli.main())
