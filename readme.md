# Lyft Bike App (starter)

A minimal Streamlit app that loads historical Bay Wheels trip data from a CSV and (optionally) shows live system status from a GBFS feed.

## Quick start (local)

1. Install **Python 3.11+** from https://www.python.org/downloads/  
   - On Windows, during install, check "Add Python to PATH".

2. In a terminal, run:
```bash
cd lyft_bike_app
python -m venv .venv
# Windows PowerShell:
.\\.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py