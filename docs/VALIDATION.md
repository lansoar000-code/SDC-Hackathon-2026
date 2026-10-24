# Validation evidence and limitations
## Live audit on 2026-10-24
The Replit public site was opened and showed the English PrepWise dashboard. Read-only HTTP checks returned:
- Health: status ok; 0 sales records, 0 distinct dates.
- Import limits: 16 MiB and 100,000 rows.
- Training: minimum 21 dates; not ready.
- Model status: untrained.
- OpenAPI: forecasting/import/sales/training/report routes; no inventory/purchasing/approval endpoint.

This establishes availability and an empty online dataset/model, not a completed cloud model demonstration. These checks did not import data, train, create forecasts or change business records.

The repository main branch still has the earlier frontend; [PR #1](https://github.com/lansoar000-code/SDC-Hackathon-2026/pull/1) contains the redesign and a fix for duplicate chart-module declarations. Synchronize and retest the final submitted revision. A published page is not proof of code/release parity.

## Earlier isolated verification
During the frontend redesign, an isolated copy of the GitHub backend passed 25 existing unittest regression tests. Coverage includes atomic imports/duplicates, CSV/XLSX validation, future-data isolation, model fingerprints/fallback, decimal prep rounding, prediction snapshots and CSV, retrospective-versus-advance metrics, JSON model restoration and legacy compatibility.

Browser checks on isolated synthetic data covered simulation, import, training, forecasts with a buffer, actual-sales feedback, history detail, CSV download, error states and a 390px layout. These checks are local historical evidence, not a fresh production acceptance run.

The earlier same-period model comparison is documented in [Data and models](DATA_AND_MODELS.md). Its synthetic metrics do not show real-world accuracy, time saved or food-waste reduction.

## Reproduce checks
```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check backend forecasting tests run.py
ruff format --check backend forecasting tests run.py
```

Tests use temporary data. Generate browser fixtures with `python tests/make_browser_fixture.py` and use an isolated instance. Do not run fixture imports against a live submission dataset without a reviewed backup and explicit intent.

## Not verified or not implemented
- Durable data/model storage through cloud republish, restart or autoscale replacement.
- Authorized-manager approval, role boundaries, actor-aware activity log or tenant separation.
- RunPod workload and proof of use.
- A cloud historical/model forecast with seeded synthetic history.
- Full repository/deployment alignment, judge access and final submission files.
- Real owner usability validation or measured business/SDG impact.

Avoid presenting local SQLite persistence tests as cloud durability, saved predictions as authorization, a proof template as actual sponsor use or a link as a successful official submission.

## Documentation cleanup checks
This cleanup consolidates duplicated documents, removes old plans/placeholders and translates retained prose into English. Application code, data, dependencies, licensing text and deployment configuration are unchanged. English prose retains the exact registered team name as a proper noun.

Verify Markdown relative links against the resulting Git tree, check that remaining files are intended, and ensure no token/secret or private contact value was copied into the declaration. This is a documentation validation task; rerunning model training is unnecessary.
