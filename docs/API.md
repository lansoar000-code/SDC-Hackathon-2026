# API contract
This is the audited forecasting API, not a proposal for new endpoints. Interactive field definitions are available at `/docs` and `/openapi.json`.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service, saved sales range/count, import limits and training readiness |
| GET | `/api/dishes` | Imported dish list |
| POST | `/api/data/import` | Multipart `file`; UTF-8 CSV or first XLSX worksheet; success 201 |
| POST | `/api/sales` | Append a JSON `records` array; success 201 |
| GET | `/api/sales` | Sales pagination; limit 1-1000 and non-negative offset |
| POST | `/api/predictions` | Create and save a forecast; success 201 |
| GET | `/api/predictions` | Saved forecasts; limit 1-100 and non-negative offset |
| GET | `/api/predictions/{prediction_id}` | Full saved snapshot |
| GET | `/api/predictions/{prediction_id}/export` | Saved forecast CSV |
| POST | `/api/models/train` | Train and compare; empty JSON or optional `cutoff_date` |
| GET | `/api/models/status` | Training status and validation report |
| GET | `/api/reports/metrics` | Matched actual/forecast comparisons and advance-forecast metrics |

## Forecast request
```json
{
  "target_date": "2026-10-25",
  "weather": "sunny",
  "is_exam_week": false,
  "has_event": false,
  "mode": "auto",
  "prep_buffer_percent": 8
}
```

Modes: `auto`, `baseline`, `demo`. Weather: `sunny`, `cloudy`, `rainy`. The prep buffer is 0-50%. Boolean fields require JSON booleans.

The response includes `prediction_id`, `created_at`, `target_date`, `source`, `model_version`, `data_origin`, `data_through`, `conditions`, `items`, totals and `warnings`. Items include stable dish ID/name, predicted sales, recommended prep, method and, for historical forecasts, the selected algorithm. Mixed results label the source and retain per-dish methods. A baseline does not apply manual weather, exam or event boosts.

Training/status responses expose validation scores rather than the complete model body. Model artifacts use `demand-selection-v2`; legacy `ridge-v1` artifacts remain readable.

## Errors and data integrity
Errors use `error.message` and optional `error.details`. Typical statuses are 400 for malformed files, 422 for invalid inputs or unavailable history, 409 for duplicate/name conflicts, 413 for excessive uploads and 404 for missing predictions. Import limits are 16 MiB / 100,000 rows and are also reported by health.

No partial import is committed when validation fails. Sale dates cannot be in the future. Dish names are rendered as text; CSV names that could be interpreted as spreadsheet formulas are escaped.

## Access boundary
No authentication, role enforcement, tenant isolation or approval endpoint is currently implemented. Never present this public prototype as a protected production restaurant system. Use synthetic data for the competition. No secrets are required for the current local forecasting inference.

The public OpenAPI inspection on 2026-10-24 contained these forecasting routes and no inventory, purchasing or approval routes. Do not add undocumented supply endpoints to slides or the proposal as completed capabilities.
