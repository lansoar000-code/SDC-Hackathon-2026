# PrepWise
Demand forecasting and meal preparation planning for small Malaysian restaurants.

## Team and competition
- Registered team: 牛马来西亚
- Domain 2: Orbyte Smart SME Challenge
- Institution: Xiamen University Malaysia
- Team leader: Lan Dongao
- Members: Shi Jiahuan, Cui Liuyang, Chen Yan and Wei Shangao
- Primary SDG: 8.2 and 8.3. Supporting target: 12.3.
- Individual contributions and declarations still require team confirmation.

## Application and submission materials
- [Live application](https://sdc-hackathon-2026--lansoar000.replit.app/)
- [Live API documentation](https://sdc-hackathon-2026--lansoar000.replit.app/docs)
- [Replit project](https://replit.com/@lansoar000/SDC-Hackathon-2026)
- [Replit proof of use](submission/SDC2026_牛马来西亚_Replit_POU.pdf)
- [Pitch deck upload](https://docs.google.com/presentation/d/1vcyDAXWv9w9mDHFz-JKE3pWYl4U1rePp/edit): uploaded to the team's Drive; anyone with the link can view.
- [Demo video](https://drive.google.com/file/d/1JNB7649TAayQP9EpgzflGmFhdiUSBBDp/view): complete 6:05.4 recording, 1080p upload copy (54,081,075 bytes); anyone with the link can view. Original audio retained. Drive preview processing may take additional time.
- [Final preliminary proposal](submission/SDC2026_牛马来西亚_Preliminary.pdf): team-approved PDF uploaded unchanged.
- [Technology / AI use declaration](submission/SDC2026_牛马来西亚_TechDeclaration.pdf): English document prepared against the official template; leader checklist review and signature pending.
- RunPod: the team confirms it has not been used. No RunPod proof or API integration is claimed.

This repository is being prepared for submission. The official portal requires a public repository and a sponsor-integration confirmation. The repository is public; qualifying sponsor use must still be resolved before formal submission. A submitted/successful status is not claimed here.

## What the prototype does
Restaurant operators import daily dish sales, request a forecast and choose a preparation buffer. The service compares a historical baseline, Ridge regression and XGBoost when sufficient historical data is available. A separate, explicitly labelled fixed-rule demo is available.

The operator can approve a saved plan using one button. The server stores a separate final plan, approval time, revision and activity events without overwriting the original prediction. The existing download link exports the approved quantities. The current interface supplies a simulated owner identity: this is not secure authentication, genuine role separation or isolation between businesses.

A future Orbyte connector could receive a restaurant's sales context, request a forecast and return an approved plan with its activity record. Live Orbyte integration is not implemented.

## Implemented capabilities
- Validated CSV/XLSX sales import, with atomic rejection of invalid batches and duplicate date/dish combinations.
- Historical baseline, Ridge and XGBoost with temporal validation and per-dish selection.
- Explicit demo mode, user-selected 0-50% preparation buffer, and separate forecast/preparation quantities.
- Saved forecasts, history and CSV exports.
- Persisted simulated approval, immutable approved plans and application activity records.
- Actual-sales feedback and MAE, WAPE and signed bias with date/dish matching.
- Reproducible team-created synthetic data generation and offline evaluation.

## Replit verification
On 25 October 2026 at approximately 01:10-01:12 MYT:
- Replit publishing status was success and the public health endpoint returned HTTP 200 / status ok.
- The public interface generated a clearly labelled synthetic forecast of 226 servings.
- The Approve plan button was observed and used; Approved and a saved timestamp appeared.
- A read-only API check confirmed submitted and approved activity events with simulated identity.

At that check, the deployed service reported zero saved sales dates and no trained model. The captured demonstration is fixed-rule synthetic output, not a live trained-model evaluation. The database has contained data at earlier points; durability across restart/republish is not established. Food-waste reduction, planning-time savings and real restaurant profit improvements have not been measured.

## Technology and external resources
| Layer | Implementation |
| --- | --- |
| Frontend | HTML, CSS and JavaScript modules |
| Backend | Python 3.12, FastAPI, Uvicorn and Pydantic |
| Storage | SQLite and JSON model artifacts |
| Forecasting | NumPy Ridge, XGBoost and historical baseline; CPU execution |
| Hosting | Replit |
| Development assistance | ChatGPT/Codex and Replit Agent |

See [resource inventory](docs/RESOURCE_DECLARATION.md), [approval scope](docs/PLAN_APPROVAL.md), [data and models](docs/DATA_AND_MODELS.md), and [architecture](docs/ARCHITECTURE.md). Older audit documents are dated snapshots; the verification above is the newer deployment observation.

No runtime generative-AI API, RunPod execution or real Orbyte connection is claimed. Declare third-party libraries, visual assets and AI development assistance in the final technology declaration.

## Run locally
Use Python 3.12 from the repository root:

```bash
python -m venv .venv
python -m pip install -r backend/requirements.txt
python run.py
```

Activate the virtual environment before installation. Open http://127.0.0.1:8000. The local launcher uses loopback; do not use it as the cloud startup command. Replit must listen on 0.0.0.0:5000 with the existing working production configuration.

## Demo
1. Open the live application and select Try demo for an explicitly synthetic example.
2. Review the forecast and suggested quantities.
3. Click Approve plan. The timestamp and approved export should appear.
4. For historical mode, generate labelled synthetic history, import it and train with at least 21 recorded dates.
5. Forecast a date after the saved history, then record synthetic actual sales for comparison.

Demo results are excluded from historical performance metrics. WAPE is an error rate, not classification accuracy. Earlier offline synthetic comparisons are not independent evidence of real-world savings.

## Checks
```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check backend forecasting tests run.py
```

The approval integration passed 33 regression tests against the GitHub-compatible backend, including 8 approval cases. Public UI generation/approval and API persistence were separately observed for the proof PDF.

## License
Project code: [Apache License 2.0](LICENSE). Third-party dependencies and external assets retain their own licenses. Do not commit credentials, real customer data, local databases, raw account emails or voucher codes.
