# PrepWise
Demand forecasting and preparation planning for small Malaysian restaurants.

## Team and competition
| Field | Status |
| --- | --- |
| Registered team name | 牛马来西亚 |
| Project | PrepWise |
| Assigned domain | Domain 2 - Orbyte Smart SME Challenge |
| Primary SDG | SDG 8, targets 8.2 and 8.3 |
| Supporting SDG | SDG 12, target 12.3; waste reduction remains a hypothesis to measure |
| Leader, member names, institutions and contributions | Team confirmation required before submission |

The registered team name is retained exactly; an official English team name has not been confirmed. Do not publish private contact details without the relevant member's consent.

## Links
- [Live application](https://sdc-hackathon-2026--lansoar000.replit.app)
- [GitHub repository](https://github.com/lansoar000-code/SDC-Hackathon-2026)
- [API documentation](https://sdc-hackathon-2026--lansoar000.replit.app/docs)
- [Submission files and naming](submission/README.md)
- [Competition readiness and remaining work](docs/COMPETITION_READINESS.md)
- Pitch deck and demo video: not completed or linked.
- RunPod endpoint and proof of use: not implemented or evidenced in the audited repository.

**Release alignment is still open.** The live site displays the English redesign, but [frontend PR #1](https://github.com/lansoar000-code/SDC-Hackathon-2026/pull/1) is unmerged. This documentation cleanup does not merge application code or deployment settings. Reconcile the final code revision with the live demonstration before submission.

## Problem and approach
Small restaurants often estimate tomorrow's portions manually from spreadsheets and recent experience. PrepWise imports daily dish sales, forecasts the next service and applies a user-selected preparation buffer. The intended benefit is more consistent planning with fewer manual steps; measured time savings and food-waste reduction have not yet been established.

The implemented journey is sales import -> validated history -> forecast -> suggested preparation -> saved snapshot -> sales feedback. A role-specific human approval step before releasing a final plan is **not implemented**. Prediction history is available, but it is not a role-aware approval/audit log.

The Domain 2 brief calls for an Orbyte-compatible automation product. A future connector could receive synthetic sales events and return an approval-ready prep plan to an SME hub. No live Orbyte connection is claimed or required by the brief.

## Implemented capabilities
- Atomic UTF-8 CSV / first-sheet XLSX import with validation and duplicate rejection.
- Explicit simulation, historical baseline, and per-dish model selection among baseline, Ridge and XGBoost.
- Date, weather, exam-week, event and 0-50% prep-buffer inputs; historical baseline does not apply invented condition multipliers.
- Separate forecast and preparation quantities, saved snapshots, history and CSV export.
- Actual-sales feedback and MAE, WAPE and signed bias, separating retrospective comparisons from advance forecasts.
- Reproducible, labelled synthetic data and temporal evaluation.

## Technology
| Layer | Actual implementation |
| --- | --- |
| Frontend | HTML, CSS, JavaScript modules |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Storage | SQLite and JSON model artifacts |
| Forecasting | NumPy Ridge, XGBoost and historical baseline, CPU |
| Hosting | Replit; no local computer or Cloudflare tunnel needed for the published URL |
| Development assistance | OpenAI ChatGPT/Codex and Replit Agent; see [resource declaration](docs/RESOURCE_DECLARATION.md) |

## Run locally
Install Python 3.12 and run from the repository root:

```bash
python -m venv .venv
```

Activate the environment:
- Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

```bash
python -m pip install -r backend/requirements.txt
python run.py
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs. The default launcher deliberately binds to loopback. Do not open the HTML file directly.

## Run on Replit
Use the Start application workflow. The server must listen on `0.0.0.0:5000`, matching the configured internal port. Production must use an explicit server startup command; the default local launcher is not suitable. See [Replit operation notes](replit.md). No inference API key is needed for the current CPU implementation.

The live health check on 2026-10-24 returned zero saved sales and no trained model. For the competition, load **team-created synthetic data only** and keep it labelled. An empty live database is not evidence that a local dataset was deployed.

## Demo workflow
1. Open the live site. Use Try demo for a fixed-rule simulation.
2. For historical/model mode, generate synthetic history as described in [Data and models](docs/DATA_AND_MODELS.md).
3. Upload the synthetic CSV and explicitly import it; choosing a file alone does not save it.
4. With at least 21 distinct saved dates, train and compare models.
5. Forecast a date after the latest saved history, review quantities and notes, and export the plan.
6. Record only synthetic actual sales for feedback. Do not claim this flow contains formal approval or real business impact.

## Documentation
- [Architecture and code map](docs/ARCHITECTURE.md)
- [API contract](docs/API.md)
- [Data, models and evaluation](docs/DATA_AND_MODELS.md)
- [Validation evidence and limitations](docs/VALIDATION.md)
- [Competition requirements and open tasks](docs/COMPETITION_READINESS.md)
- [External resources and AI-use declaration](docs/RESOURCE_DECLARATION.md)

## Checks
```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check backend forecasting tests run.py
ruff format --check backend forecasting tests run.py
```

The earlier isolated verification passed 25 tests. This documentation-only change does not claim a new cloud acceptance test.

## Submission boundaries
The repository is currently private. Provide judges access or make an explicitly reviewed public release; this cleanup does not change visibility. Do not commit credentials, local databases, model binaries, private sales, contact details or raw email content. Cloud data durability, approval/RBAC and the sponsor-use requirement remain open. The [official domain brief](https://drive.google.com/file/d/11wqbeO-HYep-DJPQ-LPZnrZfQvCgr5BU/view) requires synthetic data, permits simulated identity/roles and does not require live Orbyte access.

## License
Project code is distributed under [Apache License 2.0](LICENSE). Dependencies and external visual assets retain their own licenses and terms.
