# PrepWise on Replit

## Run

- Python 3.12; existing FastAPI backend, plain HTML/CSS/JavaScript frontend, and SQLite.
- Use the **Start application** workflow (or the Run button). It runs
  `python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000`.
- Open Preview for the app; `/docs` contains the API documentation.
- No API keys or external services are required.
- The original `python run.py` entry point remains unchanged for local use.

## Data and access

- SQLite is initialized automatically at `data/prepwise.sqlite3`.
- Trained models are stored at `models/forecast.json`.
- Start with the explicitly labeled simulation mode, or upload your own sales
  CSV/XLSX. Training requires at least 21 recorded dates.
- Do not generate synthetic records in the main database automatically.
- This is a single-restaurant app without authentication. Do not expose real
  business data to untrusted users. Public production use needs access protection
  and a durable storage/backup plan for the local database and model files.

## Checks

- `python -m unittest discover -s tests -v`
- `ruff check backend forecasting tests run.py`
- `ruff format --check backend forecasting tests run.py`

Keep the imported structure and stack; setup does not require a frontend build.
