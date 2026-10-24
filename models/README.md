# Model artifacts
Training saves `forecast.json` with model type/parameters, feature order, training cutoff, history fingerprint and validation reports. XGBoost is stored in its native JSON format; legacy Ridge JSON remains readable.

Model artifacts are generated locally and are not committed. Without a usable matching model, automatic mode uses a labelled historical baseline. See [Data and models](../docs/DATA_AND_MODELS.md) for reproducibility and evaluation limits. Persist models alongside a compatible data snapshot in a real cloud deployment.
