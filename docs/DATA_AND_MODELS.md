# Data and models
## Competition data rule
The [Domain 2 brief](https://drive.google.com/file/d/11wqbeO-HYep-DJPQ-LPZnrZfQvCgr5BU/view), Support and Data, requires team-created synthetic data with no real personal, customer or company records. Do not upload real restaurant data to the competition demo. Owner interviews or prototype usability feedback are optional validation, not permission to expose business records.

## Import fields
| Field | Meaning | Required |
| --- | --- | --- |
| `date` | Business date, YYYY-MM-DD | Yes |
| `dish_id` | Stable dish identifier | Yes |
| `dish_name` | Dish display name | Yes |
| `sales_quantity` | Observed sold portions; forecast target | Yes |
| `prepared_quantity` | Prepared portions | No |
| `waste_quantity` | Waste portions under a stated definition | No |
| `weather` | sunny/cloudy/rainy | No |
| `is_exam_week` | Boolean calendar condition | No |
| `has_event` | Boolean event condition | No |

Quantities are non-negative integers up to 1,000,000. Date/dish duplicates and inconsistent names are rejected. Missing dates are not silently converted to zero. Uploaded originals are not automatically retained; keep a source copy and generation manifest.

## Synthetic scenario
The documented reproducible dataset spans 10,000 fictional dates, 1999-06-06 to 2026-10-21, eight dishes and 80,000 rows. IDs start with `synth_`, names contain `[SYNTHETIC]`, and the UI identifies synthetic forecasts. It is not XMUM cafeteria history.

The generator uses seed 20261022 and fictional weekday, holiday, exam, event, preference and demand-noise patterns. An annual maintenance day creates explicit zero-sales records, distinct from missing dates. Weather categories are simulated; the [METMalaysia climate description](https://www.met.gov.my/en/pendidikan/iklim-malaysia/) supplied qualitative context, not observations or fitted effect coefficients. Prep is planned before realized demand; sold portions are constrained by supply and waste is prep minus sales. Oracle demand/stockout data are for audit only and must not enter forecasting features.

## Reproduce
```bash
python prepare_synthetic.py --end-date 2026-10-21
python retrain_synthetic.py
python run_synthetic.py
```

These operations generate local artifacts and train models; they are not required at web-server startup. Generation and retraining refuse to overwrite populated output directories. Use fresh `--output` and `--models` directories when repeating runs. The isolated synthetic server uses port 8002 and does not switch the ordinary website database.

Key outputs are the full sales CSV, four optional 20,000-row import batches, temporal splits, daily context, an audit-only oracle, an isolated SQLite database, a generation manifest with hashes, evaluation reports and JSON models. The whole 80,000-row sales file fits the current 100,000-row import limit if it is also below 16 MiB. Batching is optional, not mandatory.

To demonstrate model mode on the published site, explicitly import synthetic sales and train there, or deploy a reviewed matching synthetic database/model pair. Local artifacts are not automatically uploaded. On 2026-10-24, live health returned 0 sales and model status returned untrained.

## Model selection
- Baseline: recent same-weekday mean; recent-history fallback where needed.
- Ridge: standardized features, regularization with an unpenalized intercept.
- XGBoost: CPU histogram trees, 200 rounds, depth 4, learning rate 0.05, min child weight 10, subsample 0.85, column sample 1, lambda 10, alpha 0.1, seed 20261022, two threads.

All candidates use the same historical features and temporal validation dates. The lowest validation MAE wins per dish; ties prefer baseline, then Ridge, then XGBoost. At least 21 distinct saved dates are needed for training. Training and inference share feature code. Target/future sales, target prep, waste and oracle demand are excluded from inputs. Missing/invalid/stale models fall back to a labelled baseline. No pickle artifacts are used.

## Earlier same-period synthetic comparison
The earlier local comparison used 7,000 training dates, 1,500 validation dates and 1,500 rolling one-day test dates (12,000 dish-day rows). Earlier observed test-day sales may inform later test days.

| Method | MAE, portions/dish-day | WAPE, error rate | Signed bias, portions |
| --- | ---: | ---: | ---: |
| XGBoost | 9.0113 | 12.9424% | -2.9942 |
| Ridge | 12.1469 | 17.4458% | -0.6801 |
| Baseline | 14.5899 | 20.9545% | 0.1001 |

These are recorded historical results, checked against the available local comparison report during the documentation audit, not a newly rerun benchmark. The same test period had already been examined for the Ridge project. It must not be described as a new untouched test set or evidence of real restaurant accuracy. The final model trained on all 10,000 dates has seen those dates and has no independent test claim from this table.

MAE measures average absolute error; WAPE is an error rate, not accuracy, and is undefined when total actual sales are zero. Negative bias indicates underprediction. Forecasting sold portions can underestimate latent demand on stockout days. Synthetic behavior and omitted holiday/closure/supply signals limit interpretation. No reduction in food waste or staff time has yet been measured.
