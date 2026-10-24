# PrepWise on Replit
## Runtime
Python 3.12, FastAPI/Uvicorn, plain HTML/CSS/JavaScript and SQLite. No separate frontend build or remote inference key is needed.

Use Start application for development. It runs `python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000`. The internal port is 5000 and the external port is 80. The local `python run.py` launcher uses loopback port 8000 and is not a production startup command.

The production configuration must contain one deployment section with an explicit server run command and no conflicting nested run table. The user corrected this in Replit before publishing. Synchronization of that exact configuration back to GitHub remains unverified; do not overwrite it with an older import or merge.

## Published application
[Open the public website](https://sdc-hackathon-2026--lansoar000.replit.app). It is hosted in the cloud and does not require a local computer or a temporary Cloudflare tunnel to run. The free deployment has an expiry; check the publishing panel for the current date/plan. A successful deployment does not imply permanent free hosting.

## Data and models
SQLite defaults to `data/prepwise.sqlite3`; models default to `models/forecast.json`. Paths can be configured with `PREPWISE_DATABASE` and `PREPWISE_MODEL`, but changing a path does not create durable storage.

The competition site must contain only team-created synthetic records. Do not silently seed the main database, overwrite existing data or run a large synthetic training task during server startup. On 2026-10-24, the published service reported 0 saved sales and no trained model. Import reviewed synthetic history explicitly and verify model mode for the demo.

The app has no authentication. Cloud persistence, backup/restore and approval/role controls are open items, not implemented safeguards.

## Repository alignment
The English redesign is in frontend PR #1, which was still unmerged at the documentation audit. Match the submitted revision with the live frontend and production startup fix before submission. A local supply handoff must not be described as a deployed inventory capability.

## Development guidance
Keep the existing application stack and API contracts. Use the managed dependency metadata/lockfiles consistently and do not remove the project metadata required by the Replit Python installer. Never commit keys or private data. See [README](README.md), [API](docs/API.md) and [competition readiness](docs/COMPETITION_READINESS.md).
